import itertools
from . import vector, vmf, physics


def triangle_of(side):
    "extract triangle from string (returns 3 vec3)"
    triangle = [[float(i) for i in xyz.split()] for xyz in side.plane[1:-1].split(') (')]
    return tuple(map(vector.vec3, triangle))


def plane_of(A, B, C):
    """returns plane the triangle defined by A, B & C lies on"""
    normal = ((A - B) * (C - B)).normalise()
    return (normal, vector.dot(normal, A)) # normal (vec3), distance (float)


def clip(poly, plane):
    normal, distance = plane
    split_verts = {"back": [], "front": []}
    for i, A in enumerate(poly):
        B = poly[(i + 1) % len(poly)]
        A_distance = vector.dot(normal, A) - distance
        B_distance = vector.dot(normal, B) - distance
        A_behind = round(A_distance, 6) < 0
        B_behind = round(B_distance, 6) < 0
        if A_behind:
            split_verts["back"].append(A)
        else: # A is in front of the clipping plane
            split_verts["front"].append(A)
        # does the edge AB intersect the clipping plane?
        if (A_behind and not B_behind) or (B_behind and not A_behind):
            t = A_distance / (A_distance - B_distance)
            cut_point = vector.lerp(A, B, t)
            split_verts["back"].append(cut_point)
            split_verts["front"].append(cut_point)
    return split_verts


def loop_fan(vertices):
    "ploygon to triangle fan"
    out = vertices[:3]
    for vertex in vertices[3:]:
        out += [out[0], out[-1], vertex]
    return out


def loop_fan_indices(vertices):
    "polygon to triangle fan (indices only) by Exactol"
    indices = []
    for i in range(len(vertices) - 2):
        indices += [0, i + 1, i + 2]
    return indices


def disp_tris(verts, power): # copied from snake-biscuits/bsp_tool/bsp_tool.py
    """takes flat array of verts and arranges them in a patterned triangle grid
    expects verts to be an array of length ((2 ** power) + 1) ** 2"""
    power2 = 2 ** power
    power2A = power2 + 1
    power2B = power2 + 2
    power2C = power2 + 3
    tris = []
    for line in range(power2):
        line_offset = power2A * line
        for block in range(2 ** (power - 1)):
            offset = line_offset + 2 * block
            if line % 2 == 0: # |\|/|
                tris.append(verts[offset + 0])
                tris.append(verts[offset + power2A])
                tris.append(verts[offset + 1])

                tris.append(verts[offset + power2A])
                tris.append(verts[offset + power2B])
                tris.append(verts[offset + 1])

                tris.append(verts[offset + power2B])
                tris.append(verts[offset + power2C])
                tris.append(verts[offset + 1])

                tris.append(verts[offset + power2C])
                tris.append(verts[offset + 2])
                tris.append(verts[offset + 1])
            else: # |/|\|
                tris.append(verts[offset + 0])
                tris.append(verts[offset + power2A])
                tris.append(verts[offset + power2B])

                tris.append(verts[offset + 1])
                tris.append(verts[offset + 0])
                tris.append(verts[offset + power2B])

                tris.append(verts[offset + 2])
                tris.append(verts[offset + 1])
                tris.append(verts[offset + power2B])

                tris.append(verts[offset + power2C])
                tris.append(verts[offset + 2])
                tris.append(verts[offset + power2B])
    return tris


def square_neighbours(x, y, edge_length): # edge_length = (2^power) + 1
    """yields the indicies of neighbouring points in a displacement"""
    for i in range(x - 1, x + 2):
        if i >= 0 and i < edge_length:
            for j in range(y - 1, y + 2):
                if j >= 0 and j < edge_length:
                    if not (i != x and j != y):
                        yield i * edge_length + j



class solid:
    __slots__ = ('aabb', 'center', 'colour', 'displacement_triangles',
                 'displacement_vertices', 'faces', 'id', 'index_map', 'indices',
                 'is_displacement', 'planes', 'planes', 'sides', 'source',
                 'string_triangles', 'vertices')

    def __init__(self, solid_namespace): # THIS IS FOR IMPORTING FROM VMF
        """Initialise from namespace"""
        self.source = solid_namespace # preserve (for debug & accuracy)
        self.id = int(self.source.id)
        self.colour = tuple(int(x) / 255 for x in solid_namespace.editor.color.split())
        string_planes = [triangle_of(s) for s in solid_namespace.sides]
        self.planes = [plane_of(*t) for t in string_planes]
        self.is_displacement = False

        self.faces = []
        for i, plane in enumerate(self.planes):
            normal, distance = plane
            non_parallel = vector.vec3(z=-1) if normal.z != 1 else vector.vec3(y=-1)
            local_y = (non_parallel * normal).normalise()
            local_x = (local_y * normal).normalise()
            center = normal * distance
            radius = 10 ** 4 # larger than any reasonable brush
            ngon = [center + ((-local_x + local_y) * radius),
                             center + ((local_x + local_y) * radius),
                             center + ((local_x + -local_y) * radius),
                             center + ((-local_x + -local_y) * radius)]
            for other_plane in self.planes:
                if other_plane == plane: # what about the inverse plane?
                    continue
                ngon, offcut = clip(ngon, other_plane).values() # back, front
            self.faces.append(ngon)

        self.indices = []
        self.vertices = [] # [((position), (normal), (uv), (colour)), ...]
        self.index_map = []
        start_index = 0
        for face, side, plane in zip(self.faces, self.source.sides, self.planes):
            face_indices = []
            normal = plane[0]
            u_axis = side.uaxis.rpartition(' ')[0::2]
            u_vector = [float(x) for x in u_axis[0][1:-1].split()]
            u_scale = float(u_axis[1])
            v_axis = side.vaxis.rpartition(' ')[0::2]
            v_vector = [float(x) for x in v_axis[0][1:-1].split()]
            v_scale = float(v_axis[1])
            for i, vertex in enumerate(face): # regex might help here
                uv = [vector.dot(vertex, u_vector[:3]) + u_vector[-1],
                      vector.dot(vertex, v_vector[:3]) + v_vector[-1]]
                uv[0] /= u_scale
                uv[1] /= v_scale

                assembled_vertex = tuple(itertools.chain(vertex, normal, uv, self.colour))
                if assembled_vertex not in self.vertices:
                    self.vertices.append(assembled_vertex)
                    face_indices.append(len(self.vertices) - 1)
                else:
                    face_indices.append(self.vertices.index(assembled_vertex))

            face_indices = loop_fan(face_indices)
            self.index_map.append((start_index, len(face_indices)))
            self.indices += face_indices
            start_index += len(face_indices)

        global square_neighbours
        self.displacement_vertices = {} # {side_index: vertices}
        self.displacement_triangles = {} # same but repeat verts to make disp shaped triangles
        for i, side in enumerate(self.source.sides):
            if hasattr(side, "dispinfo"):
                self.source.sides[i].blend_colour = [1 - i for i in self.colour]
                self.is_displacement = True
                power = int(side.dispinfo.power)
                power2 = 2 ** power
                quad = tuple(vector.vec3(x) for x in self.faces[i])
                start = vector.vec3(eval(side.dispinfo.startposition.replace(" ", ", ")))
                if start in quad:
                    index = quad.index(start) - 1
                    quad = quad[index:] + quad[:index]
                else:
                    raise RuntimeError("Couldn't find start of displacement! (side id {})".format(side.id))
                side_dispverts = []
                A, B, C, D = quad
                DA = D - A
                CB = C - B
                distance_rows = [v for k, v in side.dispinfo.distances.__dict__.items() if k != "_line"] # skip line number
                normal_rows = [v for k, v in side.dispinfo.normals.__dict__.items() if k != "_line"]
                normals = []
                alphas = []
                for y, distance_row, normals_row in zip(itertools.count(), distance_rows, normal_rows):
                    distance_row = [float(x) for x in distance_row.split()]
                    normals_row = [*map(float, normals_row.split())]
                    left_vert = A + (DA * y / power2)
                    right_vert = B + (CB * y / power2)
                    for x, distance in zip(itertools.count(), distance_row):
                        k = x * 3
                        normal = vector.vec3(normals_row[k], normals_row[k + 1], normals_row[k + 2])
                        baryvert = vector.lerp(right_vert, left_vert, x / power2)
                        side_dispverts.append(vector.vec3(baryvert) + (distance * normal))

                # calculate displacement normals
                for x in range(power2 + 1):
                    for y in range(power2 + 1):
                        dispvert = side_dispverts[x * (power2 + 1) + y]
                        neighbour_indices = square_neighbours(x, y, power2 + 1)
                        try:
                            neighbours = [side_dispverts[i] for i in neighbour_indices]
                        except Exception as exc:
                            # f"({x}, {y}) {list(square_neighbours(x, y, power2 + 1))=}") # python 3.8
                            print("({}, {}) {}".format(x, y, list(square_neighbours(x, y, power2 + 1))))
                            print(exc) # raise traceback instead
                        normal = vector.vec3(0, 0, 1)
                        if len(neighbours) != 0:
                            normal -= dispvert - sum(neighbours, vector.vec3()) / len(neighbours)
                            normal = normal.normalise()
                        normals.append(normal)

                alphas = [float(a) for row in [v for k, v in side.dispinfo.alphas.__dict__.items() if k != "_line"] for a in row.split()]
                self.displacement_vertices[i] = [*zip(side_dispverts, alphas, normals)]
                self.displacement_triangles[i] = disp_tris(self.displacement_vertices[i], power)
                # use disp_tris when assembling vertex buffers
                # only store and update verts (full format)
                # assemble vertex format (vertex, normal, uv, colour, blend_alpha)
        if len(self.displacement_triangles) == 0:
            del self.displacement_triangles
            del self.displacement_vertices

        # all_x = [v[0].x for v in self.vertices]
        # all_y = [v[0].y for v in self.vertices]
        # all_z = [v[0].z for v in self.vertices]
        # min_x, max_x = min(all_x), max(all_x)
        # min_y, max_y = min(all_y), max(all_y)
        # min_z, max_z = min(all_z), max(all_z)
        # self.aabb = physics.aabb([min_x, min_y, min_z], [max_x, max_y, max_z])
        # self.center = (self.aabb.min + self.aabb.max) / 2

    def flip(self, plane):
        # maintain outward facing plane normals
        # presevere accuracy of planes while flipping geo
        ...

    def as_vmf_solid(self):
        # don't forget to grab your .id
        # foreach face
        #   solid.sides.append(vmf_tool.namespace(...))
        #   solid.sides.[-1].plane = '({:.f}) ({:.f}) ({:.f})'.format(*face[:3])
        ...

    def rotate(self, angles, pivot_point=None):
        # if pivot_point == None:
        #     pivot_point = self.center
        # foreach plane
        #     rotate normal
        #     recalculate distance
        # foreach vertex
        #     translate -(self.center - origin)
        #     rotate
        #     translate back
        ...

    def translate(self, offset):
        """offset is a vector"""
        # for plane in self.planes
        #     plane.distance += dot(plane.normal, offset)
        # for vertex in self.vertices
        #     vertex += offset
        ...

    def make_valid(self):
        """take all faces and ensure their verts lie on shared planes"""
        # ideally split if not convex
        # can be very expensive to correct
        # recalculate planes from tris if possible
        # if any verts not on correct planes, throw warning
        # check if solid has holes / is inverted
        ...
