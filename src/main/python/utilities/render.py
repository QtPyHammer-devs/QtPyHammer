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


# DRAWING FUNCTIONS
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
    glLineWidth(1)
    glBegin(GL_LINES)
    glColor(*colour)
    for x, y in yield_grid(limit, grid_scale):
        glVertex(x, y)
    glEnd()

def draw_origin(scale=64):
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

def draw_ray(origin, direction, distance=4096):
    glLineWidth(2)
    glBegin(GL_LINES)
    glColor(1, .75, .25)
    glVertex(*origin)
    glVertex(*(origin + direction * distance))
    glEnd()

# BUFFER TOOLS
# These two funtions work to find free segments to assign to
# render.manager method find_gap uses these functions...
#  - however! it also checks the types of neighbours to optimise draw calls
def compress(spans):
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

def free(spans, span_to_remove): # can be used to hide selection
    """remove a (start, length) span from a series of spans"""
    r_start, r_length = span_to_remove # span_to_remove is R
    r_end = r_start + r_length
    out = [] # all spans which do not intersect R
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
    """Manages OpenGL buffers and gives handles for rendering & hiding objects"""
    def __init__(self):
        self.draw_distance = 4096 * 4 # defined in settings
        self.fov = 90 # defined in settings (70 - 120)
        self.render_mode = "flat" # defined in settings
        KB = 10 ** 3
        MB = 10 ** 6
        GB = 10 ** 9
        self.memory_limit = 512 * MB # defined in settings
        # ^ can't check the physical device limit until after init_GL is called

        self.buffer_update_queue = []
        # [{"type": "brush" or "displacement"
        #   "id": brush.id or brush.side[?].id
        #   "vertex": (start, length, data),
        #   "index":  (start, length, data)}, ...]
        # ^ would a collections.namedtuple be better?

        self.vertex_buffer_size = self.memory_limit // 2
        self.index_buffer_size = self.memory_limit // 2
        self.buffer_location = {}
        # ^ renderable: {"vertex": (start, length),
        #                "index":  (start, length)}
        # where: renderable = {"type": "brush", "id": brush.id}


        self.buffer_type_spans = {"vertex": {"brush": [], "displacement": [], "model": []},
                                    "index": {"brush": [], "displacement": [], "model": []}}
        # ^ buffer: {type: [(start, length)]}
        # update:
        # self.abstract_buffer_map = ...
        # compress([*self.abstract_buffer_map["brushes"], *adding_span])
        # free(self.abstract_buffer_map["brushes"], deleting_span)
        self.hidden = {"brush": [], "displacement": []}
        # ^ type: (start, length)

    def init_GL(self, ctx): # called by parent viewport's initializeGL()
        glClearColor(0, 0, 0, 0)
        glEnable(GL_DEPTH_TEST)
        glFrontFace(GL_CW)
        glPointSize(4)
        glPolygonMode(GL_BACK, GL_LINE)
        # SHADERS
        major = glGetIntegerv(GL_MAJOR_VERSION)
        minor = glGetIntegerv(GL_MINOR_VERSION)
        GLES_MODE = False
        self.GLES_MODE = GLES_MODE
        if major >= 4 and minor >= 5:
            self.shader_version = "GLSL_450"
        elif major >= 3 and minor >= 0:
            GLES_MODE = True
            self.shader_version = "GLES_300"
        shader_folder = "shaders/{}/".format(self.shader_version)
        compile_shader = lambda s, t: compileShader(open(ctx.get_resource(shader_folder + s), "rb"), t)
        vert_brush =  compile_shader("brush.vert", GL_VERTEX_SHADER)
        vert_displacement = compile_shader("displacement.vert", GL_VERTEX_SHADER)
        frag_flat_brush = compile_shader("flat_brush.frag", GL_FRAGMENT_SHADER)
        frag_flat_displacement = compile_shader("flat_displacement.frag", GL_FRAGMENT_SHADER)
        frag_stripey_brush = compile_shader("stripey_brush.frag", GL_FRAGMENT_SHADER)
        self.shader = {"flat": {}, "stripey": {}, "textured": {}, "shaded": {}}
        # ^ style: {target: program}
        self.shader["flat"]["brush"] = compileProgram(vert_brush, frag_flat_brush)
        self.shader["flat"]["displacement"] = compileProgram(vert_displacement, frag_flat_displacement)
        self.shader["stripey"]["brush"] = compileProgram(vert_brush, frag_stripey_brush)
        for style_dict in self.shader.values():
            for program in style_dict.values():
                glLinkProgram(program)
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
        # https://github.com/snake-biscuits/QtPyHammer/wiki/Rendering:-Vertex-Format
        glEnableVertexAttribArray(0) # vertex_position
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 44, GLvoidp(0))
        glEnableVertexAttribArray(1) # vertex_normal (brush only)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_TRUE, 44, GLvoidp(12))
        # glEnableVertexAttribArray(4) # blend_alpha (displacement only)
        glVertexAttribPointer(4, 1, GL_FLOAT, GL_FALSE, 44, GLvoidp(12))
        # ^ replaces vertex_normal if displacement
        glEnableVertexAttribArray(2) # vertex_uv
        glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 44, GLvoidp(24))
        glEnableVertexAttribArray(3) # editor_colour
        glVertexAttribPointer(3, 3, GL_FLOAT, GL_FALSE, 44, GLvoidp(32))
        # Buffers
        self.VERTEX_BUFFER, self.INDEX_BUFFER = glGenBuffers(2)
        glBindBuffer(GL_ARRAY_BUFFER, self.VERTEX_BUFFER)
        glBufferData(GL_ARRAY_BUFFER, self.vertex_buffer_size, None, GL_DYNAMIC_DRAW)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.INDEX_BUFFER)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.index_buffer_size, None, GL_DYNAMIC_DRAW)

    def draw(self):
        gluPerspective(self.fov, self.aspect, 0.1, self.draw_distance)
        glUseProgram(0)
        draw_grid()
        draw_origin()
        draw_ray(vector.vec3(), vector.vec3(), 0)
        # dither transparency for tooltextures (skip, hint, trigger, clip)
        glUseProgram(self.shader[self.render_mode]["brush"])
        for start, length in self.abstract_buffer_map["index"]["brush"]:
            glDrawElements(GL_TRIANGLES, length, GL_UNSIGNED_INT, GLvoidp(start))

    def update(self):
        # update buffer data
        if len(self.buffer_update_queue) > 0:
            update = self.buffer_update_queue.pop(0)
            renderable = (update["object_type"], update["id"])
            glBufferSubData(GL_ARRAY_BUFFER, *update["vertex"])
            glBufferSubData(GL_ELEMENT_ARRAY_BUFFER, *update["index"])
            start, length, data = update["vertex"]
            vertex_span = (start, length)
            start, length, data = update["index"]
            index_span = (start, length)
            self.buffer_location[renderable] = {"vertex": vertex_span, "index": index_span}



        # update view matrix
        glUseProgram(self.shader[self.render_mode]["brush"])
        for uniform, location in self.uniform[self.render_mode]["brush"].items():
            if uniform == "matrix":
                glUniformMatrix4fv(location, 1, GL_FALSE, matrix)

    # BUFFER UPDATES
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
