import itertools

from .. import vector


def brush(brush):
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


def displacement(face):
    vertices = []
    # ^ [(*position, *normal, *uv, blend_alpha, 0, 0), ...]
    quad = tuple(vector.vec3(*P) for P in face.polygon)
    start = vector.vec3(*face.displacement.start)
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
            position = vector.vec3(*barymetric) + (normal * distance)
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


def obj_model(obj_model):
    # obj_model is expected to be an Obj object (utilities/obj.py)
    vertex_data = []  # [(*position, *normal, *uv, *colour)]
    index_data = []
    for polygon in obj_model.faces:
        indices = []
        for v_index, vn_index, vt_index in polygon:
            position = obj_model.vertices[v_index] if v_index is not None else (0, 0, 0)
            normal = obj_model.normals[vn_index] if vn_index is not None else (0, 0, 0)
            uv = obj_model.uvs[vt_index] if vt_index is not None else (0, 0)
            vertex = (*position, *normal, *uv, *(.75, .75, .75))
            if vertex not in vertex_data:
                vertex_data.append(vertex)
                indices.append(len(vertex_data) - 1)
            else:
                vertex_index = vertex_data.index(vertex)
                indices.append(vertex_index)
        index_data.extend(loop_triangle_fan(indices))
    vertex_data = tuple(itertools.chain(*vertex_data))
    return vertex_data, index_data


def loop_triangle_fan(vertices):
    "polygon to triangle fan"
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
