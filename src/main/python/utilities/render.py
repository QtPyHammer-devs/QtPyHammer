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
    """ yields lines on a grid (one vertex at a time) centered on [0, 0]
    limit: int, half the width of grid
    step: int, gap between edges"""
    # center axes
    yield 0, -limit
    yield 0, limit # +NS
    yield -limit, 0
    yield limit, 0 # +EW
    # concentric squares stepping out from center (0, 0) to limit
    for i in range(1, limit + 1, step):
        yield i, -limit
        yield i, limit # +NS
        yield -limit, i
        yield limit, i # +EW
        yield limit, -i
        yield -limit, -i # -WE
        yield -i, limit
        yield -i, -limit # -SN
    # ^ the above function is optimised for a line grid
    # another function would be required for a dot grid
    # it's also worth considering adding an offset

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
    """Manages OpenGL buffers and gives handles for rendering & hiding objects"""
    def __init__(self, parent):
        self.parent = parent # parent is expected to be a MapViewport3D
        self.queued_updates = [] # (method, *args)
        # ^ queued updates are OpenGL functions called by the parent viewport
        # specifically executed within the parent viewport's update method

        # VRAM Memory Management
        KB = 10 ** 3
        MB = 10 ** 6
        GB = 10 ** 9
        self.memory_limit = 512 * MB # user defined in settings
        # ^ be aware we can't check the video card limit until post-initializeGL
        self.vertex_buffer_size = self.memory_limit // 2
        self.index_buffer_size = self.memory_limit // 2
        self.buffer_map = {"vertex": {}, "index": {}}
        # ^ buffer: {object: (start, length)}
        # recording the in-memory location of each object is essential
        # without doing so we could not hide, edit or delete objects

        # "object" needs to be a sensible key, that works for brushes, displacements & models alike
        # mapping by brush.id should be quite functional, especially for multiplayer
        # we should only store models & other duplicate geometry (instances etc.) once and only once

        # VERTICES: needed for reallocation & offset of INDICES
        # INDICES: needed for rendering / hiding (using free function)

        ### A Qt Debug visalisation which shows the state of each buffer would be handy
        # VERTICES 0 | Brush1 | Brush2 | Displacement1 |     | LIMIT
        # INDICES  0 | B1 | B2 | Disp1 |                     | LIMIT
        # TEXTURES 0 |                                       | LIMIT
        # A tool like this would also be useful for fine tuning performance
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
        self.hidden = {} # {type: (start, length)}

    def initializeGL(self): # to be called by parent viewport's initializeGL()
        major = glGetIntegerv(GL_MAJOR_VERSION)
        minor = glGetIntegerv(GL_MINOR_VERSION)
        # ^ could get this from our Qt QGLContext Format
        GLES_MODE = False # why not just check the version?
        self.GLES_MODE = GLES_MODE
        if major >= 4 and minor >= 5:
            self.shader_version = "GLSL_450"
        elif major >= 3 and minor >= 0:
            GLES_MODE = True
            self.shader_version = "GLES_300"
        ctx = self.parent.ctx
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
        self.shader = {"flat": {}, "stripey": {}, "textured": {}, "shaded": {}}
        # ^ style: {target: program}
        self.shader["flat"]["brush"] = compileProgram(vert_brush, frag_flat_brush)
        self.shader["flat"]["displacement"] = compileProgram(vert_displacement, frag_flat_displacement)
        self.shader["stripey"]["brush"] = compileProgram(vert_brush, frag_stripey_brush)
        for style_dict in self.shader.values():
            for program in style_dict.values():
                glLinkProgram(program)
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

        # Connect vertex format to shaders
        # https://github.com/snake-biscuits/QtPyHammer/wiki/Rendering:-Vertex-Format
        # glGet(GL_MAX_VERTEX_ATTRIB_BINDINGS)
        glEnableVertexAttribArray(0) # vertex_position
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 44, GLvoidp(0))
        glEnableVertexAttribArray(1) # vertex_normal (brush only)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_TRUE, 44, GLvoidp(12))
        # glEnableVertexAttribArray(4) # blend_alpha (displacement only)
        glVertexAttribPointer(4, 1, GL_FLOAT, GL_FALSE, 44, GLvoidp(12))
        # ^ replaces vertex_normal if displacement
        # however, switching vertex formats while drawing crashes _/(;w;)\_
        glEnableVertexAttribArray(2) # vertex_uv
        glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 44, GLvoidp(24))
        glEnableVertexAttribArray(3) # editor_colour
        glVertexAttribPointer(3, 3, GL_FLOAT, GL_FALSE, 44, GLvoidp(32))
        # ^ should we grab attrib locations from shader(s)?

        # Buffers
        self.VERTEX_BUFFER, self.INDEX_BUFFER = glGenBuffers(2)
        # Vertex Buffer
        glBindBuffer(GL_ARRAY_BUFFER, self.VERTEX_BUFFER)
        glBufferData(GL_ARRAY_BUFFER, self.vertex_buffer_size, None, GL_DYNAMIC_DRAW)
        # Index Buffer
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.INDEX_BUFFER)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.index_buffer_size, None, GL_DYNAMIC_DRAW)


    def find_gaps(self, buffer="vertex", preferred_type=None, minimum_size=1):
        """Generator which yeilds a (start, length) span for each gap which meets requirements"""
        if minimum_size < 1:
            raise RuntimeError("Can't search for gap smaller than 1 byte")
        if buffer == "vertex":
            limit = self.vertex_buffer_size
        elif buffer == "index":
            limit = self.index_buffer_size
        else:
            raise RuntimeError("There is no '{}' buffer".format(buffer))
        # "spans" refers to spaces with data assigned
        # "gaps" are unused spaces in memory that data can be assigned to
        # both are recorded in the form: (starting_index, length_in_bytes)
        prev_span = (0, 0)
        prev_span_end = 0
        prev_gap = (0, 0)
        buffer_map = self.abstract_buffer_map[buffer]
        if preferred_type not in (None, *buffer_map.keys()):
            raise RuntimeError("Invalid preferred_type: {}".format(preferred_type))
        span_type = {s: t for t in buffer_map for s in buffer_map[t]}
        # ^ {"type": [*spans]} -> {span: "type"}
        span_type[prev_span] = preferred_type # always fill a gap starting at 0
        filled_spans = sorted(span_type, key=lambda s: s[0])
        # ^ all occupied spans, sorted by starting_index (span[0])
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
        """Add *brushes to the appropriate GPU buffers"""
        # the most important case is loading a fresh file which should not be overly expensive as we should have a long stretch of free memory
        # a loading bar for long updates would be handy
        # do long / large updates hang on the UI thread?
        # it would be nice if we could do all this asyncronously:
        # -- double buffering and/or using a separate thread, awaits etc.
        brushes = iter(brushes)
        vertex_writes = {} # {(start, length): data}
        offset_indices = {} # {brush: indices + offset}
        gaps = self.find_gaps(buffer="vertex") # generator
        allocating_brushes = True
        brush = next(brushes)
        vertices_size = len(brush.vertices) * 44 # 44 bytes per vertex
        while allocating_brushes:
            try:
                gap_start, gap_length = next(gaps) # NEW GAP
                allocation_start = gap_start # gap must start on a multiple of 44
                allocated_length = 0
                data = [] # [*brush.vertices]
            except StopIteration: # out of gaps
                allocating_brushes = False
                continue # quit loop
            while vertices_size < gap_length: # CHECK BRUSH
                data += brush.vertices # add to write list
                self.buffer_map["vertex"][brush] = (gap_start, vertices_size)
                # add offset to all indicies for later
                offset = lambda i: i + (gap_start // 44)
                offset_indices[brush] = list(map(offset, brush.indices))
                # update gap related variables
                allocated_length += vertices_size
                gap_start += vertices_size
                gap_length -= vertices_size
                try:
                    brush = next(brushes)
                    vertices_size = len(brush.vertices) * 44 # bytes per vertex
                except StopIteration: # out of brushes
                    allocating_brushes = False # FINAL WRITE
                    # DO NOT CONTINUE! WE STILL NEED TO WRITE!
            if allocated_length > 0: # we have data to write!
                vertex_writes[(allocation_start, allocated_length)] = data
        # check we don't have any brushes left over, if we do:
        # - check there is enough VRAM to fit the leftovers into
        # - raise an error if we are out of VRAM
        # - squeeze our leftovers into ANY gaps (no find_gaps preference)

        vertex_spans = [*self.abstract_buffer_map["vertex"]["brush"],
                        *vertex_writes.keys()]
        self.abstract_buffer_map["vertex"]["brush"] = compress(vertex_spans)
        # ^ update abstract_buffer_map with all the brushes we have prepared

        # VERTEX_BUFFER WRITES
        self.queued_updates.append(
            (glBindBuffer, *(GL_ARRAY_BUFFER, self.VERTEX_BUFFER)))
        for span, data in vertex_writes.items():
            start, length = span
            data = list(itertools.chain(*data))
            data = np.array(data, dtype=np.float32)
            self.queued_updates.append(
                (glBufferSubData, *(GL_ARRAY_BUFFER, start, length, data)))
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

        # INDEX_BUFFER WRITES
        self.queued_updates.append(
            (glBindBuffer, *(GL_ELEMENT_ARRAY_BUFFER, self.INDEX_BUFFER)))
        for span, data in index_writes.items():
            start, length = span
            data = list(itertools.chain(*data))
            data = np.array(data, dtype=np.uint32)
            self.queued_updates.append(
                (glBufferSubData, *(GL_ELEMENT_ARRAY_BUFFER, start, length, data)))
        del index_writes

##        # DEBUG show data in buffer pointed to by abstract_buffer_map
##        print("=" * 80)
##        for span in self.abstract_buffer_map["index"]["brush"]:
##            start, length = span
##            data = glGetBufferSubData(GL_ELEMENT_ARRAY_BUFFER, start, length)
##            print(np.array(data, dtype=np.uint32))
##            print("-" * 80)
##        print("=" * 80)

        # NOTES ON DEBUG PRINTS:
        # resulting buffer sizes stored in abstract map are wrong
        # indices 208 bytes, 52 integers, 17.333 triangles

        # WRITE DISPLACEMENTS TO BUFFERS
        # VERTICES & INDICES collected & offset in vertex assignment loop
