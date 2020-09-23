import itertools
import os

import numpy as np
import OpenGL.GL as gl  # imagine a python binding with gl.Begin not gl.glBegin
from OpenGL.GL.shaders import compileShader, compileProgram
from PyQt5 import QtWidgets

from .. import vector
from . import draw


class manager:
    """Manages OpenGL buffers and gives handles for rendering & hiding objects"""
    def __init__(self):
        self.draw_distance = 4096 * 4  # defined in settings
        self.fov = 90  # defined in settings (70 - 120)
        self.render_mode = "flat"  # defined in settings
        MB = 10 ** 6
        self.memory_limit = 128 * MB  # defined in settings
        # ^ can't check the physical device limit until AFTER init_GL is called
        self.buffer_update_queue = []
        # ^ buffer, start, length, data

        self.vertex_buffer_size = self.memory_limit // 2
        self.index_buffer_size = self.memory_limit // 2
        self.buffer_location = {}
        # ^ renderable: {"vertex": (start, length),
        #                "index":  (start, length)}
        # renderable = ("brush", brush.id)
        # -- OR ("displacement", (brush.id, side.id))
        self.buffer_allocation_map = {"vertex": {"brush": [],
                                                 "displacement": [],
                                                 "model": []},
                                      "index": {"brush": [],
                                                "displacement": [],
                                                "model": []}}
        # ^ buffer: {type: [(start, length)]}
        self.draw_calls = {"brush": [], "displacement": []}
        # ^ renderable_type: [span, ...]
        # span = (start, length)
        # -- what if key = (renderable_type, [(func, *args)], [(func, *args)])
        # -- ^ namedtuple("key", ["renderable_type", "setup", "tear_down"])
        self.hidden = set()  # hidden by user, not visgroup
        # ^ renderable

    def init_GL(self):
        gl.glClearColor(0.0, 0.0, 0.0, 0.0)
        gl.glEnable(gl.GL_CULL_FACE)
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glFrontFace(gl.GL_CW)
        gl.glCullFace(gl.GL_BACK)
        gl.glPointSize(4)
        gl.glPolygonMode(gl.GL_BACK, gl.GL_LINE)
        # SHADERS
        major = gl.glGetIntegerv(gl.GL_MAJOR_VERSION)
        minor = gl.glGetIntegerv(gl.GL_MINOR_VERSION)
        if major >= 4 and minor >= 5:
            self.shader_version = "GLSL_450"
        elif major >= 3 and minor >= 0:
            self.shader_version = "GLES_300"
        app = QtWidgets.QApplication.instance()
        shader_folder = os.path.join(app.folder, f"shaders/{self.shader_version}/")

        def compile_shader(f, t):
            return compileShader(open(shader_folder + f, "rb"), t)

        # shader construction could be automated some
        # the shader names have a clear format: f"{renderable}.vert", f"{style}_{renderable}.frag"
        # use os.listdir to assemble all shaders?
        vert_brush = compile_shader("brush.vert", gl.GL_VERTEX_SHADER)
        vert_displacement = compile_shader("displacement.vert", gl.GL_VERTEX_SHADER)
        frag_flat_brush = compile_shader("flat_brush.frag", gl.GL_FRAGMENT_SHADER)
        frag_flat_displacement = compile_shader("flat_displacement.frag", gl.GL_FRAGMENT_SHADER)
        frag_stripey_brush = compile_shader("stripey_brush.frag", gl.GL_FRAGMENT_SHADER)
        self.shader = {"flat": {}, "stripey": {}, "textured": {}, "shaded": {}}
        # ^ style: {target: program}
        self.shader["flat"]["brush"] = compileProgram(vert_brush, frag_flat_brush)
        self.shader["flat"]["displacement"] = compileProgram(vert_displacement, frag_flat_displacement)
        self.shader["stripey"]["brush"] = compileProgram(vert_brush, frag_stripey_brush)
        for style_dict in self.shader.values():
            for program in style_dict.values():
                gl.glLinkProgram(program)
        self.uniform = {"flat": {"brush": {}, "displacement": {}},
                        "stripey": {"brush": {}},
                        "textured": {},
                        "shaded": {}}
        # ^ style: {target: {uniform: location}}
        for style, targets in self.uniform.items():
            for target in targets:
                shader = self.shader[style][target]
                gl.glUseProgram(shader)
                self.uniform[style][target]["matrix"] = gl.glGetUniformLocation(shader, "MVP_matrix")
        gl.glUseProgram(0)
        # Buffers
        self.VERTEX_BUFFER, self.INDEX_BUFFER = gl.glGenBuffers(2)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.VERTEX_BUFFER)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, self.vertex_buffer_size, None, gl.GL_DYNAMIC_DRAW)
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.INDEX_BUFFER)
        gl.glBufferData(gl.GL_ELEMENT_ARRAY_BUFFER, self.index_buffer_size, None, gl.GL_DYNAMIC_DRAW)
        # https://github.com/snake-biscuits/QtPyHammer/wiki/Rendering:-Vertex-Format
        gl.glEnableVertexAttribArray(0)  # vertex_position
        gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, 44, gl.GLvoidp(0))
        gl.glEnableVertexAttribArray(1)  # vertex_normal (brush only)
        gl.glVertexAttribPointer(1, 3, gl.GL_FLOAT, gl.GL_TRUE, 44, gl.GLvoidp(12))
        gl.glEnableVertexAttribArray(2)  # vertex_uv
        gl.glVertexAttribPointer(2, 2, gl.GL_FLOAT, gl.GL_FALSE, 44, gl.GLvoidp(24))
        gl.glEnableVertexAttribArray(3)  # editor_colour
        gl.glVertexAttribPointer(3, 3, gl.GL_FLOAT, gl.GL_FALSE, 44, gl.GLvoidp(32))
        gl.glEnableVertexAttribArray(4)  # blend_alpha (displacement only)
        gl.glVertexAttribPointer(4, 1, gl.GL_FLOAT, gl.GL_FALSE, 44, gl.GLvoidp(32))

    def draw(self):
        gl.glUseProgram(0)
        draw.dot_grid(-2048, 2048, -2048, 2048, 64)
        draw.origin_marker()
        # TODO: dither transparency for tooltextures (skip, hint, trigger, clip)
        for renderable_type, spans in self.draw_calls.items():
            gl.glUseProgram(self.shader[self.render_mode][renderable_type])
            for start, length in spans:
                count = length // 4
                gl.glDrawElements(gl.GL_TRIANGLES, count, gl.GL_UNSIGNED_INT, gl.GLvoidp(start))

    def update(self):
        if len(self.buffer_update_queue) > 0:
            update = self.buffer_update_queue.pop(0)
            buffer, start, length, data = update
            gl.glBufferSubData(buffer, start, length, data)
        MV_matrix = gl.glGetFloatv(gl.GL_MODELVIEW_MATRIX)
        for renderable_type in self.shader[self.render_mode]:
            gl.glUseProgram(self.shader[self.render_mode][renderable_type])
            if "matrix" in self.uniform[self.render_mode][renderable_type]:
                location = self.uniform[self.render_mode][renderable_type]["matrix"]
                gl.glUniformMatrix4fv(location, 1, gl.GL_FALSE, MV_matrix)

    def track_span(self, buffer, renderable_type, span_to_track):
        target = self.buffer_allocation_map[buffer][renderable_type]
        updated_map = add_span(target, span_to_track)
        self.buffer_allocation_map[buffer][renderable_type] = updated_map

    def untrack_span(self, buffer, renderable_type, span_to_untrack):
        target = self.buffer_allocation_map[buffer][renderable_type]
        updated_map = remove_span(target, span_to_untrack)
        self.buffer_allocation_map[buffer][renderable_type] = updated_map

    def update_mapping(self, buffer, renderable_type, start, ids, lengths):
        span = (start, sum(lengths))
        self.track_span(buffer, renderable_type, span)
        if buffer == "index":
            self.draw_calls[renderable_type] = add_span(self.draw_calls[renderable_type], span)
            if renderable_type == "displacement":  # hide displacement brush
                brush_ids = {brush_id for brush_id, side_id in ids}
                brush_spans = []
                for brush_id in brush_ids:
                    span = self.buffer_location[("brush", brush_id)]["index"]
                    brush_spans = add_span(brush_spans, span)
                for span in brush_spans:
                    self.draw_calls["brush"] = remove_span(self.draw_calls["brush"], span)
        for renderable_id, length in zip(ids, lengths):
            renderable = (renderable_type, renderable_id)
            if renderable not in self.buffer_location:
                self.buffer_location[renderable] = dict()
            self.buffer_location[renderable][buffer] = (start, length)
            start += length

    def find_gaps(self, buffer="vertex", preferred_type=None, minimum_size=1):
        """Generator which yields a (start, length) span for each gap which meets requirements"""
        if minimum_size < 1:
            raise RuntimeError("Can't search for gap smaller than 1 byte")
        if buffer == "vertex":
            limit = self.vertex_buffer_size
        elif buffer == "index":
            limit = self.index_buffer_size
        else:
            raise RuntimeError(f"There is no '{buffer}' buffer")
        # "spans" refers to spaces with data assigned
        # "gaps" are unused spaces in memory that data can be assigned to
        # both are recorded in the form: (start, length)
        buffer_map = self.buffer_allocation_map[buffer]
        if sum([len(buffer_map[r]) for r in buffer_map]) == 0:
            yield (0, limit)
            return
        if preferred_type not in (None, *buffer_map.keys()):
            raise RuntimeError("Invalid preferred_type: {}".format(preferred_type))
        span_type = {start: type for type in buffer_map for start in buffer_map[type]}
        # ^ {"type": [*spans]} -> {span: "type"}
        filled_spans = sorted(span_type, key=lambda s: s[0])
        # ^ all occupied spans, sorted by start
        prev_span = filled_spans.pop(0)
        prev_span_end = sum(prev_span)
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
        if prev_span_end < limit:  # gap at tail of buffer
            gap_start = prev_span_end
            gap = (gap_start, limit - gap_start)
            if preferred_type in (None, span_type[prev_span]):
                yield gap

    def add_brushes(self, *brushes):
        brush_data = dict()
        displacement_data = dict()
        for brush in brushes:
            brush_data[brush.id] = brush_buffer_data(brush)
            if brush.is_displacement:
                for face in brush.faces:
                    if not hasattr(face, "displacement"):
                        continue
                    data = displacement_buffer_data(face)
                    displacement_data[(brush.id, face.id)] = data
        self.add_renderables("brush", brush_data)
        self.add_renderables("displacement", displacement_data)

    def add_renderables(self, renderable_type, renderables):
        """Add data to the appropriate GPU buffers"""
        # renderables = {_id: (vertices, indices)}
        vertex_gaps = self.find_gaps(buffer="vertex")
        vertex_gaps = {g: [0, [], []] for g in vertex_gaps}
        index_gaps = self.find_gaps(buffer="index", preferred_type=renderable_type)
        index_gaps = {g: [0, [], []] for g in index_gaps}
        index_gaps.update({g: [0, [], []] for g in self.find_gaps(buffer="index")})
        # ^ gap: [used_length, [ids], [data]]
        for _id in renderables:
            vertex_data, index_data = renderables[_id]
            vertex_data_length = len(vertex_data) * 4
            for gap in vertex_gaps:
                gap_start, gap_length = gap
                used_length = vertex_gaps[gap][0]
                free_length = gap_length - used_length
                if vertex_data_length <= free_length:
                    vertex_gaps[gap][0] += vertex_data_length
                    vertex_gaps[gap][1].append(_id)
                    vertex_gaps[gap][2].append(vertex_data)
                    index_offset = (gap_start + used_length) // 44
                    break
            index_data_length = len(index_data) * 4
            for gap in index_gaps:
                gap_start, gap_length = gap
                used_length = index_gaps[gap][0]
                free_length = gap_length - used_length
                if index_data_length <= free_length:
                    index_gaps[gap][0] += index_data_length
                    index_gaps[gap][1].append(_id)
                    index_data = [i + index_offset for i in index_data]
                    index_gaps[gap][2].append(index_data)
                    break
        for gap in vertex_gaps:
            if vertex_gaps[gap][0] == 0:
                continue  # no data to write in this gap
            start = gap[0]
            used_length = vertex_gaps[gap][0]
            flattened_data = list(itertools.chain(*vertex_gaps[gap][2]))
            vertex_data = np.array(flattened_data, dtype=np.float32)
            update = (gl.GL_ARRAY_BUFFER, start, used_length, vertex_data)
            self.buffer_update_queue.append(update)
            ids = vertex_gaps[gap][1]
            lengths = [len(d) * 4 for d in vertex_gaps[gap][2]]
            self.update_mapping("vertex", renderable_type, start, ids, lengths)
        for gap in index_gaps:
            if index_gaps[gap][0] == 0:
                continue  # no data to write in this gap
            start = gap[0]
            used_length = index_gaps[gap][0]
            flattened_data = list(itertools.chain(*index_gaps[gap][2]))
            index_data = np.array(flattened_data, dtype=np.uint32)
            update = (gl.GL_ELEMENT_ARRAY_BUFFER, start, used_length, index_data)
            self.buffer_update_queue.append(update)
            ids = index_gaps[gap][1]
            lengths = [len(d) * 4 for d in index_gaps[gap][2]]
            self.update_mapping("index", renderable_type, start, ids, lengths)

    def hide(self, renderable):
        # print(f"Hiding {renderable}")
        self.hidden.add(renderable)
        renderable_type = renderable[0]
        span = self.buffer_location[renderable]["index"]
        span_list = self.draw_calls[renderable_type]
        self.draw_calls[renderable_type] = remove_span(span_list, span)

    def show(self, renderable):
        # print(f"Showing {renderable}")
        self.hidden.discard(renderable)
        renderable_type = renderable[0]
        span = self.buffer_location[renderable]["index"]
        span_list = self.draw_calls[renderable_type]
        self.draw_calls[renderable_type] = add_span(span_list, span)


def brush_buffer_data(brush):
    vertices = []  # [(*position, *normal, *uv, *colour), ...]
    indices = []
    for face in brush.faces:
        polygon_indices = []
        normal = face.plane[0]
        for i, vertex in enumerate(face.polygon):
            uv = face.uv_at(vertex)
            assembled_vertex = (*vertex, *normal, *uv, *brush.colour)
            if assembled_vertex not in vertices:
                vertices.append(assembled_vertex)
                polygon_indices.append(len(vertices) - 1)
            else:
                polygon_indices.append(vertices.index(assembled_vertex))
        indices.extend(loop_triangle_fan(polygon_indices))
    vertices = tuple(itertools.chain(*vertices))
    return vertices, indices


def displacement_buffer_data(face):
    vertices = []
    # ^ [(*position, *normal, *uv, blend_alpha, 0, 0), ...]
    quad = tuple(vector.vec3(P) for P in face.polygon)
    start = vector.vec3(face.displacement.start)
    if start not in quad:  # start = closest point on quad to start
        start = sorted(quad, key=lambda P: (start - P).magnitude())[0]
    starting_index = quad.index(start) - 1
    quad = quad[starting_index:] + quad[:starting_index]
    A, B, C, D = quad
    DA = D - A
    CB = C - B
    displacement = face.displacement
    power2 = 2 ** displacement.power
    for i, normal_row, distance_row, alpha_row in zip(itertools.count(), displacement.normals,
                                                      displacement.distances, displacement.alphas):
        left_vert = A + (DA * i / power2)
        right_vert = B + (CB * i / power2)
        for j, normal, distance, alpha in zip(itertools.count(), normal_row,
                                              distance_row, alpha_row):
            barymetric = vector.lerp(right_vert, left_vert, j / power2)
            # check: do we need to apply subdivision too?
            position = vector.vec3(barymetric) + (normal * distance)
            # theta =  math.degrees(math.acos(vector.dot(face.plane[0], (0, 0, 1))))
            # normal = (normal * distance).normalise()
            # normal = normal.rotate(*[-theta * x for x in face.plane[0]])
            normal = face.plane[0]
            uv = face.uv_at(barymetric)
            alpha = alpha / 255
            vertices.append((*position, *normal, *uv, alpha, 0, 0))
    vertices = list(itertools.chain(*vertices))
    indices = disp_indices(displacement.power)
    return vertices, indices


def loop_triangle_fan(vertices):
    "ploygon to triangle fan"
    out = vertices[:3]
    for vertex in vertices[3:]:
        out += [out[0], out[-1], vertex]
    return out


def disp_indices(power):
    """output length = ((2 ** power) + 1) ** 2"""
    power2 = 2 ** power
    power2A = power2 + 1
    power2B = power2 + 2
    power2C = power2 + 3
    tris = []
    for line in range(power2):
        line_offset = power2A * line
        for block in range(2 ** (power - 1)):
            offset = line_offset + 2 * block
            if line % 2 == 0:  # |\|/|
                tris.append(offset + 0)
                tris.append(offset + power2A)
                tris.append(offset + 1)

                tris.append(offset + power2A)
                tris.append(offset + power2B)
                tris.append(offset + 1)

                tris.append(offset + power2B)
                tris.append(offset + power2C)
                tris.append(offset + 1)

                tris.append(offset + power2C)
                tris.append(offset + 2)
                tris.append(offset + 1)
            else:  # |/|\|
                tris.append(offset + 0)
                tris.append(offset + power2A)
                tris.append(offset + power2B)

                tris.append(offset + 1)
                tris.append(offset + 0)
                tris.append(offset + power2B)

                tris.append(offset + 2)
                tris.append(offset + 1)
                tris.append(offset + power2B)

                tris.append(offset + power2C)
                tris.append(offset + 2)
                tris.append(offset + power2B)
    return tris


def square_neighbours(x, y, edge_length):  # edge_length = (2^power) + 1
    """yields the indicies of neighbouring points in a displacement"""
    # for displacement smooth normal calculation (get index of neighbour in list)
    for i in range(x - 1, x + 2):
        if i >= 0 and i < edge_length:
            for j in range(y - 1, y + 2):
                if j >= 0 and j < edge_length:
                    if not (i != x and j != y):
                        yield i * edge_length + j


def add_span(span_list, span):
    # def rep(s):
    #     return(s[0], s[0] + s[1])
    # print(f"{list(map(rep, span_list))} + {rep(span)} = ")
    if len(span_list) == 0:
        return [span]
    start, length = span
    end = start + length
    for i, span in enumerate(span_list):
        # print("\t", end="")
        S, L = span
        E = S + L
        if S < end and E < start:
            # print(f"{start, end} ecclipses {S, E}")
            continue  # (S, L) is before span_to_track and doesn't touch it
        elif end < S:  # span leads (S, L) without touching it
            # print(f"{start, end} leads {S, E}")
            span_list.insert(i, (start, length))
            break
        elif S == end or E == start:  # span leads (S, L) or span tails (S, L)
            # print(f"{start, end} touches {S, E}")
            span_list.pop(i)
            new_start = min(start, S)
            span_list.insert(i, (new_start, L + length))
            break
    else:  # span tails the final (S, L) without touching it
        # print(f"{start, end}")
        span_list.append((start, length))
    # print(list(map(rep, span_list)))
    # print()
    return span_list


def remove_span(span_list, span):
    # def rep(s):
    #     return(s[0], s[0] + s[1])
    # print(f"{list(map(rep, span_list))} - {rep(span)} = ")
    start, length = span
    end = start + length
    out = []
    for S, L in span_list:
        # print("\t", end="")
        E = S + L
        # special cases
        if start <= S < E <= end:  # span ecclipses (S, L)
            # print(f"{(start, end)} ecclipses {(S, E)}")
            continue
        if S < start < end < E:  # (S, L) ecclipses span
            # print(f"{(start, end)} overlap center {(S, E)}")
            out.append((S, start - S))
            out.append((end, E - end))
            continue
        # simple cases
        if end < S:  # span leads (S, L)
            # print(f"{(start, end)} leads {(S, E)}")
            out.append((S, L))
            continue
        if start <= S < end < E:  # span overlaps start of (S, L)
            # print(f"{(start, end)} overlap start {(S, E)}")
            out.append((end, E - end))
            continue
        if S < start < E <= end:  # span overlaps tail of (S, L)
            # print(f"{(start, end)} overlaps tail {(S, E)}")
            out.append((S, start - S))
            continue
        if E <= start:  # span tails (S, L)
            # print(f"{(start, end)} tails {(S, E)}")
            out.append((S, L))
            continue
    # print(list(map(rep, out)))
    # print()
    return out
