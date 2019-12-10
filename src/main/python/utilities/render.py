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

def yield_grid(limit, step): # get "step" from Grid Scale action (MainWindow)
    for i in range(0, limit + 1, step): # centers on 0, centering on a vertex / edge would be helpful for uneven grids
        yield i, -limit
        yield i, limit # edge +NS
        yield -limit, i
        yield limit, i # edge +EW
        yield limit, -i
        yield -limit, -i # edge -WE
        yield -i, limit
        yield -i, -limit # edge -SN

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
            self.uniform["brush_flat"]["matrix"] = glGetUniformLocation(self.shader["brush_flat"], "ModelViewProjectionMatrix")
            glUseProgram(program_flat_displacement)
            self.uniform["displacement_flat"]["matrix"] = glGetUniformLocation(self.shader["displacement_flat"], "ModelViewProjectionMatrix")
            glUseProgram(program_stripey_brush)
            self.uniform["brush_stripey"]["matrix"] = glGetUniformLocation(self.shader["brush_stripey"], "ModelViewProjectionMatrix")
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
        KB = 10 ** 3
        MB = 10 ** 6
        GB = 10 ** 9 # INSANE
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
        # VRAM memory management
        self.buffer_map = {"vertex": {}, "index": {}} # buffer: {object: (start, len)}
        # ^ record indices per brush to free on deletion / edit & removing from draw_calls
        # VERTICES: needed for deletion, start of object in vertices informs offset of Indices
        # INDICES: needed for rendering, remove (start, length) span from render to hide
        # ADDING NEW BufferSubData:
        # preferably neighbouring an object of the same type (INDEX BUFFER ONLY)
        # buffer_map.get_gap(preferred_type, minimum_size) -> start of gap (/44 for index), length of gap
        # preferred_type: left neighbour is a sequence of at least 1 of the preferred_type
        # if no such gap exists give the first gap which meets min size requirements
        # if VRAM is full give an alert / error
        ### A Qt Debug visalisation which shows the state of each buffer would be handy
        # VERTICES 0 | Brush1 | Brush2 | Displacement1 |     | LIMIT
        # INDICES  0 | B1 | B2 | Disp1 |                     | LIMIT
        # TEXTURES 0 |                                       | LIMIT
        # A tool like this would also be useful for fine tuning memory limits
        self.buffer_gaps = {"vertex": set(), "index": set()} # buffer: {(start, len),}
        self.abstract_buffer_map = {"vertex": {"brushes": [], "displacements": [], "models": []},
                                    "index": {"brushes": [], "displacements": [], "models": []}}
        # buffer: {type: [(start, length)]}
        # merged into fewer stretches to help optimize malloc / defrag
        # we need to semi-regularly check how fragmented each section is
        # allow the user to set the GPU defragment rate in settings
        # double duffer each buffer and defrag in the background
        # switch to the other at the end of each defrag cycle
        # would need to take great care to ensure updates carry while changing
        # adding the switch to a "hands off" operation like saving could help...
        # to make the experience seamless

        # collate an ordered list of functions to call each frame to give to viewports
        # set program, drawElements (start, len), update "live" uniforms
        # (func, {**kwargs}) -> func(**kwargs)
        # draw_calls.append((draw_grid, {"limit": 2048, "grid_scale": 64, "colour": (.5,) * 3}))
        # draw_calls.append((draw_origin, {"scale": 64}))
            # SET STATE: brushes
            # for S, L in abstract_buffer_map[index][brushes]
            # drawElements(GL_TRIANGLES, S, L)
        self.gl_context.doneCurrent()

    def compress(spans):
        spans = list(sorted(spans, key=lambda x: x[0]))
        start, length = spans[0]
        prev_end = start + length
        out = []
        current = [start, length]
        for start, length in spans[1:]:
            end = start + length
            if start <= prev_end:
                current[1] = end - current[0]
            else:
                out.append(tuple(current))
                current = [start, length]
            prev_end = end
        out.append(tuple(current))
        return out

    def add_brushes(self, *brushes):
        """add *brushes to the appropriate GPU buffers"""
        # the most common case is loading a fresh file
        # this should not be overly expensive
        # we should have a long stretch of free memory

        # order of operations:
        # find a good gap for INDICES
        # fill this gap brush by brush until gap is filled
        # find gap(s) for the associated sets of VERITCES
        # add offsets to each set of INDICES
        # glBufferSubData(itertools.chain(*INDICES))
        # foreach consecutiveVERTICES:
        # glBufferSubData(itertools.chain(*consecutiveVERTICES))
        # repeat until all brushes are in buffers

        # do the same for displacements
        # the INDICES & VERTICES can be collected earlier
        # find gaps
        # add offsets to each set of INDICES
        # glBufferSubData(itertools.chain(*INDICES))
        # foreach consecutiveVERTICES:
        # glBufferSubData(itertools.chain(*consecutiveVERTICES))
        # note indices are a fixed length based on power
        # and INDICES can be generated as we bind them to the GPU

        # it would be nice if we could do this asyncronously
        # look into that when doing DOUBLE BUFFER DEFRAG & LOADING BARS
        vertices = []
        indices = []
        updates_map = {"vertices": {}, "indices": {}} # self.buffer_map.update(this)
        buffer_map.gap(preferred="brushes")
        # find first gap
        # track when it is filled
        # when changing gaps in VERTEX BUFFER
        for brush in brushes:
            updates_map["vertices"][brush] = (0, len(brush.indices))
            updates_map["indices"][brush] = (0, len(brush.indices))
            vertices.append(brush.vertices)
            # offset = vertices_span.start // 44
            indices.append([i + offset for i in brush.indices])
            # check if displacement
            # store displacement verts & indices
            # disp indices are generated by a function anyway
            # run this function when folding spans
            # find and fill gaps for displacements AFTER brushes
        vertices = tuple(itertools.chain(*vertices))
        indices = tuple(itertools.chain(*indices))
        self.gl_context.makeCurrent(self.offscreen_surface)

        glBufferSubData(GL_ARRAY_BUFFER, GLvoidp(...),
                        len(vertices) * 44, np.array(vertices, dtype=np.float32))
        glBufferSubData(GL_ELEMENT_ARRAY_BUFFER, GLvoidp(...),
                        len(indices) * 4, np.array(indices, dtype=np.uint32))
        self.gl_context.doneCurrent()
        # displacements
