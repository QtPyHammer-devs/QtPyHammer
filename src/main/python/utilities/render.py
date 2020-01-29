"""Bunch of OpenGL heavy code for rendering vmfs"""
import colorsys
import ctypes
import itertools
import traceback

import numpy as np
from OpenGL.GL import *
from OpenGL.GL.shaders import compileShader, compileProgram
from PyQt5 import QtGui

from . import camera, solid, vector


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

def draw_grid(limit=2048, grid_scale=64, colour=(.5, .5, .5)):
    glUseProgram(0)
    glLineWidth(1)
    glBegin(GL_LINES)
    glColor(*colour)
    for x, y in yield_grid(limit, grid_scale):
        glVertex(x, y)
    glEnd()

def draw_origin(scale=64):
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

# These two funtions work with a third to find free segments to assign to
# The render.manager class method find_gap does this
# However, it also check the types of neighbours for optimisation purposes


class manager:
    def __init__(self, parent):
        # self.gl_context = parent.context()
        # self.offscreen_surface = QtGui.QOffscreenSurface()
        # self.offscreen_surface.setFormat(self.gl_context.format())
        # self.offscreen_surface.create()
        # if not self.offscreen_surface.supportsOpenGL():
        #     raise RuntimeError("Can't run OpenGL")
        # if not self.gl_context.makeCurrent(self.offscreen_surface):
        #     raise RuntimeError("Couldn't Initialize OpenGL")
        self.parent = parent
        major = glGetIntegerv(GL_MAJOR_VERSION) # could get this from our ...
        minor = glGetIntegerv(GL_MINOR_VERSION) # Qt QGLContext Format
        GLES_MODE = False # why not just check the version
        if major >= 4 and minor >= 5:
            self.shader_version = "GLSL_450"
        elif major >= 3 and minor >= 0:
            GLES_MODE = True
            self.shader_version = "GLES_300"
        self.GLES_MODE = GLES_MODE
        shader_folder = "shaders/{}/".format(self.shader_version)
        ctx = parent.ctx
        compile_shader = lambda s, t: compileShader(open(ctx.get_resource(shader_folder + s), "rb"), t)
        # Vertex Shaders
        vert_brush =  compile_shader("brush.vert", GL_VERTEX_SHADER)
        vert_displacement = compile_shader("displacement.vert", GL_VERTEX_SHADER)
        # Fragment Shaders
        frag_flat_brush = compile_shader("flat_brush.frag", GL_FRAGMENT_SHADER)
        frag_flat_displacement = compile_shader("flat_displacement.frag", GL_FRAGMENT_SHADER)
        frag_stripey_brush = compile_shader("stripey_brush.frag", GL_FRAGMENT_SHADER)
        # Programs
        self.shader = {"flat": {}, "stripey": {}, "textured": {}, "shaded": {}}
        # ^ style: {target: program} ^ shaded is textured & shaded
        self.shader["flat"]["brush"] = compileProgram(vert_brush, frag_flat_brush)
        self.shader["flat"]["displacement"] = compileProgram(vert_displacement, frag_flat_displacement)
        self.shader["stripey"]["brush"] = compileProgram(vert_brush, frag_stripey_brush)
        for style in self.shader.values():
            for program in style.values():
                glLinkProgram(program)
        # would QtGui.QOpenGLShaderProgram share easier?

        # Uniforms
        self.uniform = {"flat": {"brush": {}, "displacement": {}},
                        "stripey": {"brush": {}},
                        "textured": {},
                        "shaded": {}}
        # ^ style: {target: {uniform: location}}
        if GLES_MODE == True:
            for style, targets in self.uniform.items():
                for target in targets:
                    glUseProgram(self.shader[style][target])
                    self.uniform[style][target]["matrix"] = glGetUniformLocation(self.shader[style][target], "ModelViewProjectionMatrix")
            glUseProgram(0)

        # Vertex Formats
        max_attribs = glGetIntegerv(GL_MAX_VERTEX_ATTRIBS)
        # should we grab attrib locations from shader(s)?
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
        ## To draw using GL_TRIANGLE_STRIP you need (start, length)
        ## per row, per displacement
        ##   9 vertex Power1 ==   396 bytes VERTICES + 96 bytes INDICES
        ##                         48 bytes INDICES GL_TRIANGLE_STRIP
        ##  25 vertex Power2 ==  1100 bytes VERTICES + 384 bytes INDICES
        ##                        160 bytes INDICES GL_TRIANGLE_STRIP
        ##  81 vertex Power3 ==  3564 bytes VERTICES + 864 bytes INDICES
        ##                        576 bytes INDICES GL_TRIANGLE_STRIP
        ## 289 vertex Power4 == 12716 bytes VERTICES + 2176 bytes INDICES
        ##                       6144 bytes INDICES GL_TRIANGLE_STRIP
        ## 100 Power 2 Displacements = 110 000 ~110KB VERTICES
        ##                              16 000 ~ 16KB INDICES
        ##                             126 000 ~126KB VERTICES & INDICES
        ## 100 Power 3 Displacements = 356 400 ~360KB VERTICES
        ##                              57 600 ~ 58KB INDICES
        ##                             414 000 ~414KB VERTICES & INDICES
        ## 100 Power2 + 100 Power3 = 110 000 + 356 400 = 466 400
        ##                          ~467KB VERTICES
        ##                            16 000 +  57 600 =  73 600
        ##                           ~74KB INDICES
        ##                           466 400 +  73 600 = 540 000
        ##                          ~540KB VERTICES & INDICES
        ## 200 Cube Brushes + 100 Power2 Displacement + 100 Power3 DIsplacements
        ## ~640KB of VRAM (536.8KB VERTICES + 102.4KB INDICES)
        # pl_upward_d.vmf has:
        # 558 Displacement Brushes & 1890 Non-Displacement Brushes

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
        self.buffer_map = {"vertex": {}, "index": {}}
        # buffer: {object: (start, length)}
        # object = brush: {side_index: (start, length)} for displacements
        # what about mapping by brush id?
        # recording this makes hiding, deleting and adding geometry easy
        # this system is good for brushes & displacements but for instances...
        # we should only store models & other often duplicated geometry once
        # we key the hash (a pointer if using CPython) of each brush
        # how do we key displacements? brush.faces[i].dispinfo ?
        # it needs to be sensible for singling out when deleting & selecting
        # hiding individual faces seems like a bad idea
        # knowing the offset of the INDICES a brush and using that brush's ...
        # internal map of it's indices should make "highlighting" a face easy

        # VERTICES: needed for reallocation & offset of INDICES
        # INDICES: needed for rendering / hiding (using free function)

        ### A Qt Debug visalisation which shows the state of each buffer would be handy
        # VERTICES 0 | Brush1 | Brush2 | Displacement1 |     | LIMIT
        # INDICES  0 | B1 | B2 | Disp1 |                     | LIMIT
        # TEXTURES 0 |                                       | LIMIT
        # A tool like this would also be useful for fine tuning memory limits
        self.abstract_buffer_map = {"vertex": {"brush": [], "displacement": [], "model": []},
                                    "index": {"brush": [], "displacement": [], "model": []}}
        # buffer: {type: [(start, length)]}
        # used to simplify draw calls and keep track of any fragmentation
        # fragmentation of the index buffer means slower framerate

        # update method:
        # self.abstract_buffer_map = ...
        # compress([*self.abstract_buffer_map["brushes"], *adding_span])
        # free(self.abstract_buffer_map["brushes"], deleting_span)

        # should we double buffer each buffer and defragment in the background?
        # switching to the other at the end of each complete defrag cycle
        # leaving generous gaps between types would be clever
        # adding the switch to a "hands off" operation like saving could help...
        # to make the experience seamless

        # collate an ordered list of draw functions for viewports
        # draw calls need to ask the render manager what to draw (and what to skip)
        # set program, drawElements (start, len), [update uniform(s)]
        # (func, {**kwargs}) -> func(**kwargs)
        # draw_calls.append((draw_grid, {"limit": 2048, "grid_scale": 64, "colour": (.5,) * 3}))
        # draw_calls.append((draw_origin, {"scale": 64}))
            # SET STATE: brushes
            # for S, L in abstract_buffer_map["index"]["brush"]
            # drawElements(GL_TRIANGLES, S, L)

    def find_gaps(self, buffer="vertex", preferred_type=None, minimum_size=1):
        """Generator which yeilds a (start, length) span for each gap which meets requirements"""
        if minimum_size < 1:
            raise RuntimeError("Can't search for gap smaller than 1 byte")
        buffer_map = self.abstract_buffer_map[buffer]
        if preferred_type not in (None, *buffer_map.keys()):
            raise RuntimeError("Can't search for gap of type {}".format(preferred_type))
        if buffer == "vertex":
            limit = self.vertex_buffer_size
        elif buffer == "index":
            limit = self.index_buffer_size
        else:
            raise RuntimeError("Buffer {} is not mapped".format(buffer))
        span_type = {span: _type for _type in buffer_map for span in buffer_map[_type]}
        # ^ {"type": [*spans]} -> {span: "type"}
        filled_spans = sorted(span_type, key=lambda s: s[0])
        # ^ all spans filled by objects of all types, sorted by span[0] (start)
        # spans are spaces with data assigned
        # gaps are free spaces data can be assigned to
        prev_span = (0, 0)
        span_type[prev_span] = preferred_type
        # ^ if buffer is empty, use it
        prev_span_end = 0
        prev_gap = (0, 0)
        for span in filled_spans:
            span_start, span_length = span
            gap_start = prev_span_end + 1
            gap_length = span_start - gap_start
            if gap_length >= minimum_size:
                gap = (gap_start, gap_length)
                if preferred_type in (None, span_type[span], span_type[prev_span]):
                    yield gap
            prev_span = span
            prev_span_end = span_start + span_length
        if prev_span_end < limit: # final gap
            gap_start = prev_span_end
            gap = (gap_start, limit - gap_start)
            if preferred_type in (None, span_type[prev_span]):
                    yield gap

    def add_brushes(self, *brushes):
        """add *brushes to the appropriate GPU buffers"""
        # the most important case is loading a fresh file
        # which should not be overly expensive
        # as we should have a long stretch of free memory
        brushes = list(brushes) # for pop method
        vertex_writes = {} # {(start, length): data}
        offset_indices = {} # brush: indices + offset
        for gap in self.find_gaps(buffer="vertex"):
            gap_start, gap_length = gap
            true_gap_start = gap_start
            # gap must start on a multiple of 44
            gap_sufficient = True
            data = [] # itertools.chain([brush.vertices])
            while gap_sufficient and len(brushes) > 0:
                brush = brushes[0]
                # does brush have displacement data?
                # if so, assign its verts and offset its indices too
                vertices_size = len(brush.vertices) * 44 # bytes per vertex
                if vertices_size > gap_length:
                    gap_sufficient = False
                    continue # go to next gap
                data += brush.vertices
                self.buffer_map["vertex"][brush] = (gap_start, vertices_size)
                offset = lambda i: i + (gap_start // 44)
                offset_indices[brush] = list(map(offset, brush.indices))
                gap_start += vertices_size
                gap_length -= vertices_size
                brushes.pop(0) # this brush will be written, go to next brush
            vertex_writes[(true_gap_start, len(data) * 4)] = data
        if len(brushes) > 0: # couldn't pack all brushes with above method
            gaps = [g for g in self.find_gaps(buffer="vertex")]
            # take remaining brushes, if any, and pack as best as possible
            # if any brush is too large for any gap
            # not any(gap.length >= brush.span.length)
            # we are out of VRAM, raise Error OR
            # if sum(gap.lengths) == sum(brush.lengths): ADD ON NEXT DEFRAG
        vertex_spans = [*self.abstract_buffer_map["vertex"]["brush"],
                        *vertex_writes.keys()]
        self.abstract_buffer_map["vertex"]["brush"] = compress(vertex_spans)

        self.parent.makeCurrent()
        for span, data in vertex_writes.items():
            start, length = span
            data = list(itertools.chain(*data))
            # ^ [(*position, *normal, *uv, *colour)] => [*vertex]
            glBufferSubData(GL_ARRAY_BUFFER, start, length,
                            np.array(data, dtype=np.float32))
        self.parent.doneCurrent()
        del vertex_writes

        # ^^ offset_indices = {brush: indices + offset} ^^
        index_writes = {} # {(start, length): data}
        for gap in self.find_gaps(buffer="index", preferred_type="brush"):
            gap_start, gap_length = gap
            true_gap_start = gap_start
            gap_sufficient = True
            data = [] # itertools.chain([brush.indices + offset])
            while gap_sufficient and len(offset_indices) > 0:
                brush, indices = list(offset_indices.items())[0]
                indices_size = len(indices) * 4 # sizeof(np.uint32)
                if indices_size > gap_length:
                    gap_sufficient = False
                    continue # go to next gap
                # implied else
                self.buffer_map["index"][brush] = (gap_start, indices_size)
                data.append(indices)
                gap_start += indices_size
                gap_length -= indices_size
                offset_indices.pop(brush) # data for brush has been allocated
            index_writes[(true_gap_start, len(data) * 4)] = data
        if len(offset_indices) > 0: # lazy method couldn't pack every brush
            gaps = [g for g in self.find_gaps(buffer="index")]
            # check total_gap_length < remaining_data_length
        index_spans = [*self.abstract_buffer_map["index"]["brush"],
                       *index_writes.keys()]
        self.abstract_buffer_map["index"]["brush"] = compress(index_spans)

        self.parent.makeCurrent()
        for span, data in index_writes.items():
            start, length = span
            data = list(itertools.chain(*data))
            # ^ [[brush.indices], [brush.indices]] => [*brush.indices]
            glBufferSubData(GL_ELEMENT_ARRAY_BUFFER, start, length,
                            np.array(data, dtype=np.float32))
            print(np.array(data, dtype=np.float32))
            print("-" * 80)
        del index_writes

        print("=" * 80)
        for span in self.abstract_buffer_map["index"]["brush"]:
            start, length = span
            data = glGetBufferSubData(GL_ELEMENT_ARRAY_BUFFER, start, length)
            print(np.array(data, dtype=np.float32))
            print("-" * 80)
        print("=" * 80)
        self.parent.doneCurrent()

        # resulting buffer sizes stored in abstract map are wrong
        # indices 208 bytes, 52 integers, 17.333 triangles

        # now do the displacements
        # VERTICES & INDICES collected & offset in vertex assignment loop

        # it would be nice if we could do all this asyncronously
        # double buffering and/or using a separate thread, awaits etc.

    # def share_context(self, other_context):
    #     other_context.setShareContext(self.gl_context)
    #     other_context.setFormat(self.gl_context.format())
    #     other_context.create()
    #     if not self.gl_context.areSharing(self.gl_context, other_context):
    #         raise RuntimeError("GL BROKES, TELL A PROGRAMMER!")
