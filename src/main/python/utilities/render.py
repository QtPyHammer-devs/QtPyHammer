"""Bunch of OpenGL heavy code for rendering vmfs"""
from collections import namedtuple
import colorsys
import ctypes
import itertools
import traceback

import numpy as np
from OpenGL.GL import *
from OpenGL.GL.shaders import compileShader, compileProgram
from OpenGL.GLU import *
from PyQt5 import QtGui

from . import camera, solid, vector


# DRAWING FUNCTIONS
def yield_grid(limit, step): # "step" = Grid Scale (MainWindow action)
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
    # it's also worth considering adding an offset / origin point

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
        # ^ buffer, start, length, data
        self.mappings_update_queue = []
        # ^ type, ids, lengths

        self.vertex_buffer_size = self.memory_limit // 2
        self.index_buffer_size = self.memory_limit // 2
        self.buffer_location = {}
        # ^ renderable: {"vertex": (start, length),
        #                "index":  (start, length)}
        # where: renderable = {"type": "brush", "id": brush.id}

        self.buffer_allocation_map = {"vertex": {"brush": [],
                                                 "displacement": [],
                                                 "model": []},
                                      "index": {"brush": [],
                                                "displacement": [],
                                                "model": []}}
        # ^ buffer: {type: [(start, length)]}
        self.hidden = {"brush": [], "displacement": [], "model": []}
        # ^ type: (start, length)
        # DOES NOT YET AFFECT RENDER
        self.vertex_format_size = 44

    def init_GL(self, ctx): # called by parent viewport's initializeGL()
        glClearColor(0.0, 0.0, 0.0, 0.0)
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
        # Buffers
        self.VERTEX_BUFFER, self.INDEX_BUFFER = glGenBuffers(2)
        glBindBuffer(GL_ARRAY_BUFFER, self.VERTEX_BUFFER)
        glBufferData(GL_ARRAY_BUFFER, self.vertex_buffer_size, None, GL_DYNAMIC_DRAW)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.INDEX_BUFFER)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.index_buffer_size, None, GL_DYNAMIC_DRAW)
        # https://github.com/snake-biscuits/QtPyHammer/wiki/Rendering:-Vertex-Format
        glEnableVertexAttribArray(0) # vertex_position
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 44, GLvoidp(0))
        glEnableVertexAttribArray(1) # vertex_normal (brush only)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_TRUE, 44, GLvoidp(12))
        # glEnableVertexAttribArray(4) # blend_alpha (displacement only)
        # glVertexAttribPointer(4, 1, GL_FLOAT, GL_FALSE, 44, GLvoidp(12))
        # ^ replaces vertex_normal if displacement
        glEnableVertexAttribArray(2) # vertex_uv
        glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 44, GLvoidp(24))
        glEnableVertexAttribArray(3) # editor_colour
        glVertexAttribPointer(3, 3, GL_FLOAT, GL_FALSE, 44, GLvoidp(32))

    def draw(self):
        glUseProgram(0)
        draw_grid()
        draw_origin()
        draw_ray(vector.vec3(), vector.vec3(), 0)
        # TODO: dither transparency for tooltextures (skip, hint, trigger, clip)
        glUseProgram(self.shader[self.render_mode]["brush"])
##        for start, length in self.buffer_allocation_map["index"]["brush"]:
##            glDrawElements(GL_TRIANGLES, length, GL_UNSIGNED_INT, GLvoidp(start))
        glDrawArrays(GL_POINTS, 0, 9000)

    def update(self):
        # update buffer data
        if len(self.buffer_update_queue) > 0:
            update = self.buffer_update_queue.pop(0)
            buffer, start, length, data = update
            glBufferSubData(buffer, start, length, data)
            buffer = {GL_ARRAY_BUFFER: "vertex",
                      GL_ELEMENT_ARRAY_BUFFER: "index"}[buffer]
            # ^ ternary operator, but can be extended for other buffer types
            # -- if Key then buffer = Value
            mapping = self.mappings_update_queue.pop(0)
            renderable_type, ids, lengths = mapping
            self.track_span(buffer, renderable_type, (start, length))
            # ^ add to self.buffer_allocation_map
            for renderable_id, length in zip(ids, lengths):
                key = (renderable_type, renderable_id)
                if key not in self.buffer_location:
                    self.buffer_location[key] = dict()
                self.buffer_location[key][buffer] = (start, length)
                start += length
        # update view matrix
        MV_matrix = glGetFloatv(GL_MODELVIEW_MATRIX)
        glUseProgram(self.shader[self.render_mode]["brush"])
        if "matrix" in self.uniform[self.render_mode]["brush"]:
            location = self.uniform[self.render_mode]["brush"]["matrix"]
            glUniformMatrix4fv(location, 1, GL_FALSE, MV_matrix)

    # modify self.buffer_allocation_map
    # WORKING
    def track_span(self, buffer, renderable_type, span_to_track):
        start, length = span_to_track
        end = start + length
        target = self.buffer_allocation_map[buffer][renderable_type]
        if len(target) == 0:
            self.buffer_allocation_map[buffer][renderable_type] = [span_to_track]
            return
        for i, span in enumerate(target):
            S, L = span
            E = S + L
            # we can safely assume no spans overlap
            # self.find_gaps checks that
            # but self.find_gaps doesn't update the map
            # we don't update the map until the buffer is updated
            if S < end and E < start:
                continue # (S, L) is before span_to_track and doesn't touch it
            elif S == end: # span_to_track leads (S, L)
                old = target.pop(i)
                target.insert(i, (S, L + length))
            elif E == start: # span_to_track tails (S, L) 
                S, L = target.pop(i)
                target.insert(i, (S, L + length))
            elif S > end:
                break # past the end of span_to_track [we're done!]

    def untrack_span(self, buffer, renderable_type, span_to_untrack):
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
    # WORKING END

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
        buffer_map = self.buffer_allocation_map[buffer]
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

    # --> add_brushes --> buffer_update_queue & mapping_update_queue
    # in future this will be reworked for all renderable types
    # -- variable vertex format size (& gap_start alignment)
    # -- possibly different vertex & index data acquisition
    def add_brushes(self, *brushes):
        """Add *brushes to the appropriate GPU buffers"""
        vertex_gaps = {g: [0, [], []] for g in self.find_gaps(buffer="vertex")}
        index_gaps = {g: [0, [], []] for g in self.find_gaps(buffer="index", preferred_type="brush")}
        # ^ gap: [used_length, [ids], [data]]
        for brush in brushes:
            vertex_data_length = len(brush.vertices) * self.vertex_format_size
            for gap in vertex_gaps:
                gap_start, gap_length = gap
                used_length = vertex_gaps[gap][0]
                free_length = gap_length - used_length
                if vertex_data_length <= free_length:
                    vertex_gaps[gap][0] += vertex_data_length # used_length
                    vertex_gaps[gap][1].append(brush.id) # brush ids
                    vertex_data = list(itertools.chain(*brush.vertices))
                    vertex_gaps[gap][2].append(vertex_data) # data
                    index_offset = gap_start // self.vertex_format_size
                    break
            index_data_length = len(brush.indices) * 4
            for gap in index_gaps:
                gap_start, gap_length = gap
                used_length = index_gaps[gap][0]
                free_length = gap_length - used_length
                if index_data_length <= free_length:
                    index_gaps[gap][0] += index_data_length # used length
                    index_gaps[gap][1].append(brush.id) # brush ids
                    index_data = [i + index_offset for i in brush.indices]
                    index_gaps[gap][2].append(index_data) # data
                    break
        for gap in vertex_gaps:
            if vertex_gaps[gap][0] == 0: # used length
                continue
            flattened_data = list(itertools.chain(*vertex_gaps[gap][2]))
            vertex_data = np.array(flattened_data, dtype=np.float32)
            update = (GL_ARRAY_BUFFER, gap_start, used_length, vertex_data)
            self.buffer_update_queue.append(update)
            print(used_length, len(vertex_data))
            ids = vertex_gaps[gap][1]
            lengths = [len(d) * self.vertex_format_size for d in vertex_gaps[gap][2]]
            mapping = ("brush", ids, tuple(lengths))
            self.mappings_update_queue.append(mapping)
        for gap in index_gaps:
            if index_gaps[gap][0] == 0: # used length
                continue
            flattened_data = list(itertools.chain(*vertex_gaps[gap][2]))
            index_data = np.array(flattened_data, dtype=np.uint32)
            update = (GL_ELEMENT_ARRAY_BUFFER, gap_start, used_length, index_data)
            self.buffer_update_queue.append(update)
            ids = index_gaps[gap][1]
            lengths = [len(d) * 4 for d in index_gaps[gap][2]]
            mapping = ("brush", ids, tuple(lengths))
            self.mappings_update_queue.append(mapping)
