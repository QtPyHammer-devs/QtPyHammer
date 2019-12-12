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


def draw_elements(spans=[]):
    for start, length in spans:
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

# BUFFER TOOLS
def compress(spans): # simplify memory map
    """Combine a series of spans into as few (start, length) spans as possible
    This is to minimise calls read, write & draw calls to OpenGL buffers"""
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

def free(spans, span_to_remove): # remove from memory map
    """remove a (start, length) span from a series of spans"""
    r_start, r_length = span_to_remove # R
    r_end = r_start + r_length
    out = []
    for start, length in spans: # current span
        end = start + length # current end
        if r_start <= start < end <= r_end:
            continue # R eclipses current span
        else:
            if start < r_start:
                new_end = min([end, r_start])
                out.append((start, new_end - start)) # segment before R
            if r_end < end:
                new_start = max([start, r_end])
                out.append((new_start, end - new_start)) # segment after R
    return out


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

        ### --- 44 bytes SOLID FACE VERTEX FORMAT --- ###
        # -- 12 bytes  (3 float32)  Position
        # -- 12 bytes  (3 float32)  Normal
        # -- 8  bytes  (2 float32)  UV
        # -- 12 bytes  (3 float32)  Colour
        ## 1 Tri  == 132 bytes VERTICES +  12 bytes INDICES
        ## 1 Quad == 176 bytes VERTICES +  24 bytes INDICES
        ## 1 Cube == 352 bytes VERTICES + 144 bytes INDICES
        ## 200 Cube Solids = 70 400 ~ 71KB VERTICES
        ##                   28 800 ~ 29KB INDICES
        ##                   99 200 ~100KB VERTICES & INDICES


        ### --- 44 bytes DISPLACEMENT VERTEX FORMAT --- ###
        # -- 12 bytes  (3 float32)  Position
        # -- 4  bytes  (1 float32)  Alpha
        # -- 8  bytes  (2 padding)  0x0000
        # -- 8  bytes  (2 float32)  UV
        # -- 12 bytes  (3 float32)  Colour

        ## |\|/|\|/|\|/|\|/|
        ## |/|\|/|\|/|\|/|\|
        ## |\|/|\|/|\|/|\|/|  Power 3
        ## |/|\|/|\|/|\|/|\|
        ## |\|/|\|/|\|/|\|/|  |\|/|\|/|  Power 2
        ## |/|\|/|\|/|\|/|\|  |/|\|/|\|
        ## |\|/|\|/|\|/|\|/|  |\|/|\|/|  |\|/| Power 1
        ## |/|\|/|\|/|\|/|\|  |/|\|/|\|  |/|\|

        ## 2 ^ power = quads per row
        ## 2 ^ power * 2 = tris per row
        ## 2 ^ power * 2 * 2^power = tris per displacement
        ## 2 ^ power * 2 * 2^power * 3 = vertices referenced per displacement

        ## GL_TRIANGLES
        ## 2^power * 2 triangles * 2^power rows * 3 vertices * 4 bytes
        ## lambda power: ((2 ** power) ** 2) * 24

        ## GL_TRIANGLE STRIP
        ## (2^power + 1) * 2 vertices * 2^power rows * 4 bytes
        ## lambda power: ((2 ** power) + 1) * (2 ** power) * 8

        ## to draw need (start, length) per row per displacement
        
        
        ##   9 * 44 Power1 ==   396 bytes VERTICES + 96 bytes INDICES
        ##                       48 bytes INDICES GL_TRIANGLE_STRIP
        
        ##  25 * 44 Power2 ==  1100 bytes VERTICES + 384 bytes INDICES
        ##                      160 bytes INDICES GL_TRIANGLE_STRIP
        
        ##  81 * 44 Power3 ==  3564 bytes VERTICES + 864 bytes INDICES
        ##                      576 bytes INDICES GL_TRIANGLE_STRIP
        
        ## 289 * 44 Power4 == 12716 bytes VERTICES + 2176 bytes INDICES
        ##                     6144 bytes INDICES GL_TRIANGLE_STRIP

        ## 100 Power 2 Displacements = 110 000 ~110KB VERTICES
        ##                              16 000 ~ 16KB INDICES
        ##                             126 000 ~126KB VERTICES & INDICES
        ## 100 Power 3 Displacements = 356 400 ~360KB VERTICES
        
        ## 100 Power2 + 100 Power3 = 110 000 + 356 400 = 466 400
        ##                          ~467KB VERTICES
        ##                            16 000 +  57 600 =  73 600
        ##                           ~74KB INDICES
        ##                           466 400 +  73 600 = 540 000
        ##                          ~540KB VERTICES & INDICES

        ## 200 Cube Brushes + 100 Power2 Displacement + 100 Power3 DIsplacements
        ## ~640KB of VRAM (536.8KB VERTICES + 102.4KB INDICES)

        # pl_upward_d.vmf
        # 558 Displacement Brushes & 1890 Non-Displacement Brushes

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
        GB = 10 ** 9
        self.memory_limit = 512 * MB # user defined in settings
        VERTEX_BUFFER, INDEX_BUFFER = glGenBuffers(2)
        self.vertex_buffer_size = self.memory_limit // 2 # halve again if double buffering
        self.index_buffer_size = self.memory_limit // 2 # could change the ratio
        # Vertex Buffer
        glBindBuffer(GL_ARRAY_BUFFER, VERTEX_BUFFER)
        glBufferData(GL_ARRAY_BUFFER, self.vertex_buffer_size, None, GL_DYNAMIC_DRAW)
        # Index Buffer
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, INDEX_BUFFER)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.index_buffer_size, None, GL_DYNAMIC_DRAW)
        # VRAM Memory Management
        self.buffer_map = {"vertex": {}, "index": {}} # buffer: {object: (start, len)}
        # ^ index span of each brush ^
        # recording this makes hiding, deleting and adding geometry easy
        # this system is good for brushes & displacements but for instances...
        # we should only store models & other often duplicated geometry once
        # we key the hash (a pointer if using CPython) of each brush
        # how do we key displacements? brush.faces[i].dispinfo ?
        # it needs to be sensible for singling out when deleting & selecting
        # hiding individual faces seems like a bad idea
        # knowing the offset of the INDICES a brush and using that brush's ...
        # internal map of it's indices should make "highlighting" a face easy

        # VERTICES: needed for deletion, start of object in VERTICES informs offset of INDICES
        # INDICES: needed for rendering, remove (start, length) span from render to hide

        ### A Qt Debug visalisation which shows the state of each buffer would be handy
        # VERTICES 0 | Brush1 | Brush2 | Displacement1 |     | LIMIT
        # INDICES  0 | B1 | B2 | Disp1 |                     | LIMIT
        # TEXTURES 0 |                                       | LIMIT
        # A tool like this would also be useful for fine tuning memory limits
        self.abstract_buffer_map = {"vertex": {"brush": [], "displacement": [], "model": []},
                                    "index": {"brush": [], "displacement": [], "model": []}}
        # buffer: {type: [(start, length)]}
        # used to simplify draw calls and keep track of any fragmentation
        # fragmentation would lead to a lot of draw calls with identical state

        # update method:
        # self.abstract_buffer_map = ...
        # compress([*self.abstract_buffer_map["brushes"], *adding_span])
        # free(self.abstract_buffer_map["brushes"], deleting_span)

        # should we double buffer each buffer and defragment in the background?
        # switching to the other at the end of each complete defrag cycle
        # leaving generous gaps between types would be clever
        # adding the switch to a "hands off" operation like saving could help...
        # to make the experience seamless

        # collate an ordered list of functions to call each frame to give to viewports
        # draw calls need to ask the render manager what is hidden
        # set program, drawElements (start, len), [update uniform(s)]
        # (func, {**kwargs}) -> func(**kwargs)
        # draw_calls.append((draw_grid, {"limit": 2048, "grid_scale": 64, "colour": (.5,) * 3}))
        # draw_calls.append((draw_origin, {"scale": 64}))
            # SET STATE: brushes
            # for S, L in abstract_buffer_map[index][brushes]
            # drawElements(GL_TRIANGLES, S, L)
        self.gl_context.doneCurrent()

    def find_gap(self, buffer="vertex", preferred_type=None, minimum_size=1):
        # return (start, length) of gap
        # start of VERTEX gap /44 for gives INDICES offset
        # preferred_type: left neighbour is a sequence of at least 1 of the preferred_type
        # if preferred_type cannot be satistifed, default to first map of length > minimum size
        # if VRAM is full give an alert / error
        # self.abstract_buffer_map[buffer] = {"type": spans}
        # inverse map would be {span: "type"}
        if minimum_size < 1:
            raise RuntimeError("Can't search for gap smaller than 1 byte")
        if preffered_type not in (None, "brush", "displacement", "model"):
            raise RuntimeError("Can't search for gap of type {}".format(preferred_type))
        if buffer == "vertex":
            limit = self.vertex_buffer_size
        elif buffer == "index":
            limit = self.index_buffer_size
        else:
            raise RuntimeError("Buffer {} is not mapped".format(buffer))
        buffer_map = self.abstract_buffer_map[buffer]
        if preffered_type != None:
            good_neighbours = buffer_map[preffered_type]
            other_neighbours = itertools.chain(v for k, v in buffer_map if k != preffered_type)
        else:
            good_neighbours = itertools.chain(*buffer_map.values())
            other_neighbours = []
        good_neighbours = list(sorted(good_neighbours, key=lambda s: s[0]))
        prev_span = (0, 0)
        prev_end = 0
        for span in good_neighbours:
            # gap BEFORE
            # IS THERE A GAP HERE?
            # need to know nearest < LESS THAN end
            gap_length = start - prev_end
            # gap AFTER
            # IS THERE A GAP HERE?
            ...

    def add_brushes(self, *brushes):
        """add *brushes to the appropriate GPU buffers"""
        # the most common case is loading a fresh file
        # this should not be overly expensive
        # we should have a long stretch of free memory

        # order of operations:
        # find a good gap for INDICES

        # fill this gap brush by brush until gap is filled
        # find gap(s) for the associated sets of VERITCES
        # add vertices to the buffer_map & abstract_buffer_map
        # assemble vertex data until gap is full
        # add offsets to each set of INDICES matched with each set of VERTICES
        # glBufferSubData(itertools.chain(*VERTICES))
        # find gaps for indices
        # aim for keeping same types close
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
