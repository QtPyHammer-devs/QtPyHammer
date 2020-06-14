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

        # queue for self.update_buffers()
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
        # Buffers
        self.VERTEX_BUFFER, self.INDEX_BUFFER = glGenBuffers(2)
        glBindBuffer(GL_ARRAY_BUFFER, self.VERTEX_BUFFER)
        glBufferData(GL_ARRAY_BUFFER, self.vertex_buffer_size, None, GL_DYNAMIC_DRAW)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.INDEX_BUFFER)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.index_buffer_size, None, GL_DYNAMIC_DRAW)
        # https://github.com/snake-biscuits/QtPyHammer/wiki/Rendering:-Vertex-Format
        self.vertex_format_size = 44
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
            self.update_buffers(self, update)
        # update view matrix
        MV_matrix = glGetFloatv(GL_MODELVIEW_MATRIX)
        P_matrix = glGetFloatv(GL_PROJECTION_MATRIX)
        glUseProgram(self.shader[self.render_mode]["brush"])
        if "matrix" in self.uniform[self.render_mode]["brush"]:
            location = self.uniform[self.render_mode]["brush"]["matrix"]
            glUniformMatrix4fv(location, 1, GL_FALSE, MV_matrix)

    # BUFFER UPDATES
    def update_buffers(self, update):
        """update data in buffers and draw calls"""
        # {"type": "brush" or "displacement" or model
        #  "ids": [id, ...],
        #  "spans": [{"vertex": (start, length),
        #             "index": (start, length)}, ...]
        #  "vertex": (start, length, data),
        #  "index": (start, length, data)}
        # ^ zip together
        glBufferSubData(GL_ARRAY_BUFFER, *update["vertex"])
        glBufferSubData(GL_ELEMENT_ARRAY_BUFFER, *update["index"])
        ids, spans = update["ids"], update["spans"]
        for renderable_id, span in zip(ids, spans):
            # span = {"vertex": (start, length), "index": (start, length)}
            self.buffer_location[identifier] = span
        self.track_span("vertex", "brush", update["vertex"][:2])
        self.track_span("index", "brush", update["index"][:2])

    # modify self.buffer_allocation_map
    # WORKING
    def track_span(self, buffer, renderable_type, span_to_track):
        start, length = span_to_track
        end = start + length
        target = self.buffer_allocation_map[buffer][renderable_type]
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
        # aiming to be a generator
        # until async is implemented
        gaps = self.find_gaps(buffer="vertex") # generator
        brushes = iter(brushes)
        def next_brush():
            out = {"brush": next(brushes),
                   "identifier": {"type": "brush", "id": brush.id}}
            flat_vertex_data = itertools.chain(*brush.vertices)
            out["vertex_data"] = np.array(flat_vertex_data, dtype=np.float32)
            out["vertex_length"] = len(brush.vertices) * self.vertex_format_size
            out["index_data"] = np.array(brush.indices, dtype=np.uint32)
            out["index_length"] = len(brush.indices) * 4
            return out
        brush = next_brush()
        allocating = True
        for gap in gaps:
            pass
            # brush["vertex_length"]
            # brush["index_length"]
            # yield an buffer_update for the queue
            # -- for each gap filled
