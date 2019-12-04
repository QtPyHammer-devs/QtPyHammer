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


def draw_buffer_ranges(program=0, ranges=[]):
    glUseProgram(program)
    # set vertex format
    for start, length in ranges:
        glDrawElements(GL_TRIANGLES, length, GL_UNSIGNED_INT, GLvoidp(start))

def draw_buffer_ranges_GLES(program=0, ranges=[], matrix_loc=0):
    glUseProgram(program)
    # matrix = glGetFloatv(GL_PROJECTION_MATRIX)
    # # ^ grabbing from cpu-side memory would be better ^
    glUniformMatrix4fv(matrix_loc, 1, GL_FALSE, matrix)
    for start, length in ranges:
        glDrawElements(GL_TRIANGLES, length, GL_UNSIGNED_INT, GLvoidp(start))

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


class manager:
    def __init__(self, viewport, ctx):
        self.gl_context = QtGui.QOpenGLContext()
        self.gl_context.setShareContext(viewport.context())
        # self.gl_context.setFormat( some format )
        self.gl_context.create()
        self.offscreen_surface = QtGui.QOffscreenSurface()
        self.offscreen_surface.setFormat(self.gl_context.format())
        self.offscreen_surface.create()
        if not self.offscreen_surface.supportsOpenGL():
            raise RuntimeError("Can't run OpenGL")
        if not self.gl_context.makeCurrent(self.offscreen_surface):
            raise RuntimeError("Couldn't Initialise open GL")

        major = glGetIntegerv(GL_MAJOR_VERSION)
        minor = glGetIntegerv(GL_MINOR_VERSION)
        GLES_MODE = False
        if major >= 4 and minor >= 5:
            self.shader_version = "GLSL_450"
        elif major >= 3 and minor >= 0:
            GLES_MODE = True
            self.shader_version = "GLES_300"
        self.GLES_MODE = GLES_MODE
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
        self.shader = {} # name: program
        self.shader["brush_flat"] = compileProgram(vert_brush, frag_flat_brush)
        self.shader["displacement_flat"] = compileProgram(vert_displacement, frag_flat_displacement)
        self.shader["brush_stripey"] = compileProgram(vert_brush, frag_stripey_brush)
        glLinkProgram(self.shader["brush_flat"])
        glLinkProgram(self.shader["displacement_flat"])
        glLinkProgram(self.shader["brush_stripey"])

        # Uniforms
        self.uniform = {} # shader: {uniform_name: location, ...}
        if GLES_MODE == True:
            glUseProgram(program_flat_brush)
            self.uniform["brush_flat"]["matrix"] = glGetUniformLocation(self.shader["brush_flat"], 'ModelViewProjectionMatrix')
            glUseProgram(program_flat_displacement)
            self.uniform["displacement_flat"]["matrix"] = glGetUniformLocation(self.shader["displacement_flat"], 'ModelViewProjectionMatrix')
            glUseProgram(program_stripey_brush)
            self.uniform["brush_stripey"]["matrix"] = glGetUniformLocation(self.shader["brush_stripey"], 'ModelViewProjectionMatrix')
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
        self.memory_limit = 512 * MB # defined in settings
        VERTEX_BUFFER, INDEX_BUFFER = glGenBuffers(2)
        # why do we generate and bind these buffers?
        # could we detatch them to affect other buffers?
        # Vertex Buffer
        glBindBuffer(GL_ARRAY_BUFFER, VERTEX_BUFFER)
        glBufferData(GL_ARRAY_BUFFER, self.memory_limit // 2, None, GL_DYNAMIC_DRAW)
        # Index Buffer
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, INDEX_BUFFER)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.memory_limit // 2, None, GL_DYNAMIC_DRAW)
        self.buffer_map = {} # (start, len): object, ...
        # ^ this only refers to the index buffer
        # since we don't share vertices between objects
        self.cursor = {"vertices": 0, "indices": 0}
        self.greatest_index = 0

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
        self.gl_context.doneCurrent()

    def defrag_buffer(self):
        gaps = []
        gap_start = 0
        for start, length in self.buffer_map:
            if start > gap_start:
                gaps.append((gap_start, start))
            gap_start = start + length
        return gaps
        # grab from the tail and shift into the gaps
        # shifting vertices would mean changing a bunch of indices
        # if updating a brush you may want to keep old verts and add some more in a gap

    def add_brushes(self, *brushes):
        vertices = []
        indices = []
        for brush in brushes:
            self.buffer_map[brush] = (self.greatest_index, len(brush.indices))
            vertices.append(brush.vertices)
            indices.append([i + self.latest_index for i in brush.indices])
            self.latest_index += len(brush.indices)
        vertices = tuple(itertools.chain(*vertices))
        indices = tuple(itertools.chain(*indices))
        self.gl_context.makeCurrent(self.offscreen_surface)
        glBufferSubData(GL_ARRAY_BUFFER, GLvoidp(self.cursor["vertices"]),
                        len(vertices) * 44, np.array(vertices, dtype=np.float32))
        glBufferSubData(GL_ELEMENT_ARRAY_BUFFER, GLvoidp(self.cursor["indices"]),
                        len(vertices) * 44, np.array(indices, dtype=np.uint32))
        self.gl_context.doneCurrent()
        # displacements
