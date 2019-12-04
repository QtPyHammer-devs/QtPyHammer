"""Bunch of OpenGL heavy code for rendering vmfs"""
import colorsys
import ctypes
import itertools
import traceback

import numpy as np
from OpenGL.GL import *
from OpenGL.GL.shaders import compileShader, compileProgram
from PyQt5 import QtGui

from . import camera, solid, vector, vmf


def draw_brushes(viewport, program=0, ranges=[]):
    glUseProgram(program)
    # set vertex format
    for start, length in ranges:
        glDrawElements(GL_TRIANGLES, length, GL_UNSIGNED_INT, GLvoidp(start))

def draw_brushes_GLES(viewport, program=0, matrix_loc=0, ranges=[]):
    glUseProgram(program)
    matrix = glGetFloatv(GL_PROJECTION_MATRIX)
    # ^ grabbing from cpu-side memory would be better ^
    glUniformMatrix4fv(matrix_loc, 1, GL_FALSE, matrix)
    # set vertex format
    for start, length in ranges:
        glDrawElements(GL_TRIANGLES, length, GL_UNSIGNED_INT, GLvoidp(start))

def draw_displacements(viewport, program=0, ranges=[]):
    ... # WIP

def yield_grid(limit, step): # get 'step' from Grid Scale action (MainWindow)
    for i in range(0, limit + 1, step): # centers on 0, centering on a vertex / edge would be helpful for uneven grids
        yield i, -limit
        yield i, limit
        yield -limit, i
        yield limit, i
        yield limit, -i
        yield -limit, -i
        yield -i, limit
        yield -i, -limit

def draw_grid(viewport, limit=2048, grid_scale=64, colour=(.5, .5, .5)):
    glUseProgram(0)
    glLineWidth(1)
    glBegin(GL_LINES)
    glColor(*colour)
    for x, y in yield_grid(limit, grid_scale):
        glVertex(x, y)
    glEnd()

def draw_origin(viewport, scale=64):
    glUseProgram(0)
    glLineWidth(2)
    glBegin(GL_LINES)
    glColor(1, 0, 0)
    glVertex(0, 0, 0)
    glVertex(scale, 0, 0)
    glColor(0, 1, 0)
    glVertex(0, 0, 0)
    glVertex(0, scale, 0)
    glColor(0, 0, 1)
    glVertex(0, 0, 0)
    glVertex(0, 0, scale)
    glEnd()

def vmf_setup(viewport, vmf_object, ctx):
    string_solids = []
    ... # passed in by MapTab

    solids = []
    global solid
    for ss in string_solids:
        try:
            solids.append(solid.solid(ss))
        except Exception as exc:
            print("Invalid solid! (id {})".format(ss.id))
            traceback.print_exc(limit=3)
            print("*" * 80)
##            raise exc

    major = glGetIntegerv(GL_MAJOR_VERSION)
    minor = glGetIntegerv(GL_MINOR_VERSION)
    GLES_MODE = False
    if major >= 4 and minor >= 5: # GLSL 450
        version = "GLSL_450"
    elif major >= 3 and minor >= 0: # GLES 3.00
        GLES_MODE = True
        version = "GLES_300"
    viewport.GLES_MODE = GLES_MODE
    shader_folder = "shaders/{}/".format(version)
    compile_shader = lambda s, t: compileShader(open(ctx.get_resource(shader_folder + s), "rb"), t)
    # Vertex Shaders
    vert_shader_brush =  compile_shader("brush.vert", GL_VERTEX_SHADER)
    vert_shader_displacement = compile_shader("displacement.vert", GL_VERTEX_SHADER)
    # Fragment Shaders
    frag_shader_flat_brush = compile_shader("flat_brush.frag", GL_FRAGMENT_SHADER)
    frag_shader_flat_displacement = compile_shader("flat_displacement.frag", GL_FRAGMENT_SHADER)
    frag_shader_stripey_brush = compile_shader("stripey_brush.frag", GL_FRAGMENT_SHADER)
    # Programs
    program_flat_brush = compileProgram(vert_shader_brush, frag_shader_flat_brush)
    program_flat_displacement = compileProgram(vert_shader_displacement, frag_shader_flat_displacement)
    program_stripey_brush = compileProgram(vert_shader_brush, frag_shader_stripey_brush)
    glLinkProgram(program_flat_brush)
    glLinkProgram(program_flat_displacement)
    glLinkProgram(program_stripey_brush)

    # Uniforms
    if GLES_MODE == True:
        glUseProgram(program_flat_brush)
        uniform_matrix_flat_brush = glGetUniformLocation(program_flat_brush, 'ModelViewProjectionMatrix')
        glUseProgram(program_flat_displacement)
        uniform_matrix_flat_displacement = glGetUniformLocation(program_flat_displacement, 'ModelViewProjectionMatrix')
        glUseProgram(program_stripey_brush)
        uniform_matrix_stripey_brush = glGetUniformLocation(program_stripey_brush, 'ModelViewProjectionMatrix')
        glUseProgram(0)

    vertices = []
    indices = []
    solid_map = dict()
    for brush in [s for s in solids if not s.is_displacement]:
        solid_map[brush.id] = (len(indices), len(brush.indices))
        indices += [len(vertices) + i for i in brush.indices]
        vertices += brush.vertices
    brush_len = len(indices)
    for brush in [s for s in solids if s.is_displacement]: # displacements
        for side, verts in brush.displacement_vertices.items():
            power = int(brush.source.sides[side].dispinfo.power)
            raw_indices = range(len(indices), len(indices) + len(verts))
            indices += solid.disp_tris(raw_indices, power)
            vertices += verts

    disp_len = len(indices) - brush_len
    vertices = tuple(itertools.chain(*vertices))
    # remember what index ranges are for "UNHIDE ALL"

    # Vertex Buffer
    VERTEX_BUFFER, INDEX_BUFFER = glGenBuffers(2)
    glBindBuffer(GL_ARRAY_BUFFER, VERTEX_BUFFER)
    glBufferData(GL_ARRAY_BUFFER, len(vertices) * 4,
                 np.array(vertices, dtype=np.float32), GL_DYNAMIC_DRAW)
    # Index Buffer
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, INDEX_BUFFER)
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, len(indices) * 4,
                 np.array(indices, dtype=np.uint32), GL_DYNAMIC_DRAW)
    # Vertex Format
    max_attribs = glGetIntegerv(GL_MAX_VERTEX_ATTRIBS)
    # grab indices from the shaders?
    # hand this to the draw functions
    glEnableVertexAttribArray(0) # vertex_position
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 44, GLvoidp(0))
    glEnableVertexAttribArray(1) # vertex_normal (brush only)
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_TRUE, 44, GLvoidp(12))
    # glEnableVertexAttribArray(4) # blend_alpha (displacement only)
    glVertexAttribPointer(4, 1, GL_FLOAT, GL_FALSE, 44, GLvoidp(12))
    # ^ replaces vertex_normal if displacement ^
    glEnableVertexAttribArray(2) # vertex_uv
    glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 44, GLvoidp(24))
    glEnableVertexAttribArray(3) # editor_colour
    glVertexAttribPointer(3, 3, GL_FLOAT, GL_FALSE, 44, GLvoidp(32))

    # keep handles to the buffers, shaders & uniforms someplace safe
    # viewport.buffers = [VERTEX_BUFFER, INDEX_BUFFER]
    # viewport.programs = [program_flat_brush, program_flat_displacement,
    #                      program_stripey_brush]

    viewport.draw_calls[draw_grid] = {"limit": 2048, "grid_scale":64, "colour": (.5,) * 3}
    viewport.draw_calls[draw_origin] = {"scale": 64}
    if not GLES_MODE:
        global draw_brushes
        viewport.draw_calls[draw_brushes] = {"program": program_stripey_brush,
                                             "ranges": [(0, brush_len)]}
                                             # ^ split to hide brushes
        # viewport.draw_calls[draw_displacements] = {"program": program_flat_displacement,
        #                               "ranges": [(brush_len + 1, disp_len)]}
    else:
        global draw_brushes_GLES
        viewport.draw_calls[draw_brushes_GLES] = {"program": program_flat_brush,
                                        "ranges": [(0, brush_len)],
                                        "matrix_loc": uniform_matrix_flat_brush}

def merge_spans(*spans):
    spans = sorted(spans, key=lambda s: s[0]) # order by start
    start = spans[0][0] # start of first span
    for span in spans:
        start, length = span


class manager:
    def __init__(self, ctx):
        self.gl_context = QtGui.QOpenGLContext()
        self.offscreen_surface = QtGui.QOffscreenSurface()
        if not self.offscreen_surface.supportsOpenGL():
            raise RuntimeError("Can't run OpenGL")
        self.gl_context.setFormat(self.offscreen_surface.format())
        self.gl_context.create()
        print(self.gl_context.makeCurrent(self.offscreen_surface))

        major = glGetIntegerv(GL_MAJOR_VERSION)
        minor = glGetIntegerv(GL_MINOR_VERSION)
        GLES_MODE = False
        if major >= 4 and minor >= 5:
            self.shader_version = "GLSL_450"
        elif major >= 3 and minor >= 0:
            GLES_MODE = True
            self.shader_version = "GLES_300"
        viewport.GLES_MODE = GLES_MODE
        shader_folder = "shaders/{}/".format(self.shader_version)
        compile_shader = lambda s, t: compileShader(open(ctx.get_resource(shader_folder + s), "rb"), t)
        # Vertex Shaders
        vert_brush =  compile_shader("brush.vert", GL_VERTEX_SHADER)
        vert_displacement = compile_shader("displacement.vert", GL_VERTEX_SHADER)
        # Fragment Shaders
        frag_flat_brush = compile_shader("flat_brush.frag", GL_FRAGMENT_SHADER)
        frag_flat_displacement = compile_shader("flat_displacement.frag", GL_FRAGMENT_SHADER)
        frag_stripey_brush = compile_shader("stripey_brush.frag", GL_FRAGMENT_SHADER)
        # Programs
        self.shaders = {} # name: program
        self.shader["brush_flat"] = compileProgram(vert_brush, frag_flat_brush)
        self.shader["displacement_flat"] = compileProgram(vert_displacement, frag_flat_displacement)
        self.shader["brush_stripey"] = compileProgram(vert_brush, frag_stripey_brush)
        glLinkProgram(self.shader["brush_flat"])
        glLinkProgram(self.shader["displacement_flat"])
        glLinkProgram(self.shader["brush_stripey"])

        # Uniforms
        self.uniforms = {} # shader: {uniform_name: location, ...}
        if GLES_MODE == True:
            glUseProgram(program_flat_brush)
            self.uniforms["brush_flat"]["matrix"] = glGetUniformLocation(self.shader["brush_flat"], 'ModelViewProjectionMatrix')
            glUseProgram(program_flat_displacement)
            self.uniforms["displacement_flat"]["matrix"] = glGetUniformLocation(self.shader["displacement_flat"], 'ModelViewProjectionMatrix')
            glUseProgram(program_stripey_brush)
            self.uniforms["brush_stripey"]["matrix"] = glGetUniformLocation(self.shader["brush_stripey"], 'ModelViewProjectionMatrix')
            glUseProgram(0)

        # Vertex Formats
        max_attribs = glGetIntegerv(GL_MAX_VERTEX_ATTRIBS)
        # grab indices from the shaders?
        glEnableVertexAttribArray(0) # vertex_position
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 44, GLvoidp(0))
        glEnableVertexAttribArray(1) # vertex_normal (brush only)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_TRUE, 44, GLvoidp(12))
        # glEnableVertexAttribArray(4) # blend_alpha (displacement only)
        glVertexAttribPointer(4, 1, GL_FLOAT, GL_FALSE, 44, GLvoidp(12))
        # ^ replaces vertex_normal if displacement ^
        glEnableVertexAttribArray(2) # vertex_uv
        glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 44, GLvoidp(24))
        glEnableVertexAttribArray(3) # editor_colour
        glVertexAttribPointer(3, 3, GL_FLOAT, GL_FALSE, 44, GLvoidp(32))

        # Buffers
        KB = 1024
        MB = 1024 * 1024
        memory_limit = 512 * MB # defined in settings
        VERTEX_BUFFER, INDEX_BUFFER = glGenBuffers(2)
        # Vertex Buffer
        glBindBuffer(GL_ARRAY_BUFFER, VERTEX_BUFFER) # GL_DYNAMIC_DRAW
        # Index Buffer
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, INDEX_BUFFER)
        self.gl_context.doneCurrent()

    def add_brushes(self, *brushes):
        vertices = []
        indices = []
        for brush in brushes:
            vertices.append(brush.vertices)
            # add greatest current index to indices
            indices.append(brush.indices)
            # add brush to buffer map
