import itertools
import vector
import sys
sys.path.insert(0, '../')
import vmf_tool
sys.path.insert(0, 'render/')
import physics

def triangle_of(side):
    "extract triangle from string (returns 3 vec3)"
    triangle = [[float(i) for i in xyz.split()] for xyz in side.plane[1:-1].split(') (')]
    return tuple(map(vector.vec3, triangle))

def plane_of(A, B, C):
    """returns plane the triangle defined by A, B & C lies on"""
    normal = ((A - B) * (C - B)).normalise()
    return (normal, vector.dot(normal, A))

def loop_fan(vertices):
    "ploygon to triangle fan"
    out = vertices[:3]
    for vertex in vertices[3:]:
        out += [out[0], out[-1], vertex]
    return out

def loop_fan_indices(vertices):
    "polygon to triangle fan (indices only) by Exactol"
    indices = []
    for i in range(1, len(vertices) - 1):
        indices += [0, i, i + 1]
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
            else: #|/|\|
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


class solid:
    def __init__(self, string_solid):
        """Initialise from string, nested dict or namespace"""
        if isinstance(string_solid, vmf_tool.namespace):
            pass
        elif isinstance(string_solid, dict):
            source = vmf_tool.namespace(string_solid)
        elif isinstance(string_solid, str):
            source = vmf_tool.namespace_from(string_solid)
        else:
            raise RuntimeError(f'Tried to create solid from invalid type: {type(string_solid)}')
        self.string_solid = string_solid # preserve for debug & export
        self.colour = tuple(int(x) / 255 for x in string_solid.editor.color.split())
        self.string_triangles = [triangle_of(s) for s in string_solid.sides]
        self.string_vertices = list(itertools.chain(*self.string_triangles))
        # does not contain every point, some will be missing
        # goldrush contains an example (start of stage 2, arch behind cart)
        self.planes = [plane_of(*t) for t in self.string_triangles] # ((Normal XYZ), Dist)
        self.is_displacement = False
        self.sides = []
        for side in self.string_solid.sides:
            del side.id
            del side.plane
            self.sides.append(vmf_tool.namespace(side))

        # match vertices to plane intersections
        # tabulate edges where 2 planes meet
        # identify holes (1 vertex edges)
        # calculate missing vertices from holes (if any)

        # faces namespace
        # face([plane, texture_data([material, uvs, lightmap_scale]), vertices])
        self.faces = []
        for i, tri in enumerate(self.string_triangles):
            plane = self.planes[i]
            face = list(tri)
            for vertex in self.string_vertices:
                if vertex not in face:
                    if plane[1] - 1 < vector.dot(vertex, plane[0]) < plane[1] + 1:
                        face.append(vertex)
            face = vector.sort_clockwise(face, plane[0])
            self.faces.append(face)

        # displacements next
        # loop fan OR disp pattern
        self.face_tri_map = []
        triangles = []
        last_index = 0
        for face in self.faces:
            face_tris = loop_fan(face)
            self.face_tri_map.append((last_index, last_index + len(face_tris)))
            last_index += len(face_tris)
            triangles += face_tris
        self.triangles = tuple(triangles)

        # move triangle assembley to renderer (make immutable)
        self.displacement_triangles = {}
        # {side_index: vertices}
        self.displacement_vertices = {}
        for i, side in enumerate(string_solid.sides):
            if hasattr(side, 'dispinfo'):
                self.sides[i].blend_colour = [1 - i for i in self.colour]
                self.is_displacement = True
                power = int(side.dispinfo.power)
                power2 = 2 ** power
                quad = tuple(vector.vec3(x) for x in self.faces[i])
                start = vector.vec3(eval(side.dispinfo.startposition.replace(' ', ', ')))
                if start in quad:
                    index = quad.index(start) - 1
                    quad = quad[index:] + quad[:index]
                else:
                    raise RuntimeError(f"Couldn't find start of displacement! (side id {side.id})")
                side_dispverts = []
                A, B, C, D = quad
                DA = D - A
                CB = C - B
                distance_rows = side.dispinfo.distances.__dict__.values()
                normal_rows = side.dispinfo.normals.__dict__.values()
                normals = []
                alphas = []
                for y, distances_row, normals_row in zip(itertools.count(), distance_rows, normal_rows):
                    distances_row = [float(x) for x in distances_row.split()]
                    normals_row = [*map(float, normals_row.split())]
                    left_vert = A + (DA * y / power2)
                    right_vert = B + (CB * y / power2)
                    for x, distance in zip(itertools.count(), distances_row):
                        k = x * 3
                        normal = vector.vec3(normals_row[k], normals_row[k + 1], normals_row[k + 2])
                        baryvert = vector.lerp(right_vert, left_vert, x / power2)
                        side_dispverts.append(vector.vec3(baryvert) + (distance * normal))

                def square_neighbours(x, y, edge_length):
                    """square is the length of an edge"""
                    for i in range(x - 1, x + 2):
                        if i >= 0 and i < edge_length:
                            for j in range(y - 1, y + 2):
                                if j >= 0 and j < edge_length:
                                    if not (i != x and j != y):
                                        yield i * edge_length + j
                
                for x in range(power2 + 1):
                    for y in range(power2 + 1):
                        dispvert = side_dispverts[x * (power2 + 1) + y]
                        neighbour_indices = square_neighbours(x, y, power2 + 1)
                        try:
                            neighbours = [side_dispverts[i] for i in neighbour_indices]
                        except Exception as exc:
                            print(f'({x} {y}) {list(square_neighbours(x, y, power2 + 1))}')
                            print(exc)
                        normal = vector.vec3(0, 0, 1)
                        if len(neighbours) != 0:
                            normal -= dispvert - sum(neighbours, vector.vec3()) / len(neighbours)
                            normal = normal.normalise()
                        normals.append(normal)

                alphas = [float(a) for row in side.dispinfo.alphas.__dict__.values() for a in row.split()]
                self.displacement_vertices[i] = [*zip(side_dispverts, alphas, normals)]
                self.displacement_triangles[i] = disp_tris(self.displacement_vertices[i], power)
                # use disp_tris when assembling vertex buffers
                # only store and update verts (full format)
                # assemble vertex format (vertex, normal, uv, colour, blend_alpha)

        if len(self.displacement_triangles) == 0:
            del self.displacement_triangles
            del self.displacement_vertices

        self.indices = []
        self.vertices = [] # [((position), (normal), (uv)), ...]
        # put all formatted vertices in list
        # record indices for each face loop
        # convert face loops to triangle fans
        # store (start, len) for each face [index buffer range mapping]
        # store full index strip
        self.index_map = []
        start_index = 0
        for face, side, plane in zip(self.faces, string_solid.sides, self.planes):
            face_indices = []
            normal = plane[0]
            for i, vertex in enumerate(face):
                u_axis = side.uaxis.rpartition(' ')[0::2]
                u_vector = [float(x) for x in u_axis[0][1:-1].split()]
                u_scale = float(u_axis[1])
                v_axis = side.vaxis.rpartition(' ')[0::2]
                v_vector = [float(x) for x in v_axis[0][1:-1].split()]
                v_scale = float(v_axis[1])
                uv = [vector.dot(vertex, u_vector[:3]) + u_vector[-1],
                      vector.dot(vertex, v_vector[:3]) + v_vector[-1]]
                uv[0] /= u_scale
                uv[1] /= v_scale

                assembled_vertex = tuple(itertools.chain(*zip(vertex, normal, uv, self.colour)))
                if assembled_vertex not in self.string_vertices:
                    self.vertices.append(assembled_vertex)
                    face_indices.append(len(self.vertices) - 1)
                else:
                    face_indices.append(self.vertices.index(assembled_vertex))
            face_indices = loop_fan_indices(face_indices)
            self.index_map.append((start_index, len(face_indices)))
            start_index += len(face_indices)
            self.indices += face_indices
        
        all_x = [v[0] for v in self.string_vertices]
        all_y = [v[1] for v in self.string_vertices]
        all_z = [v[2] for v in self.string_vertices]
        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)
        min_z, max_z = min(all_z), max(all_z)
        self.aabb = physics.aabb([min_x, min_y, min_z], [max_x, max_y, max_z])
        self.center = (self.aabb.min + self.aabb.max) / 2

        # DISPLACEMENTS (IF PRESENT)
        # {side_index: displacement}
        # SEE HAMMER DISP DRAW MODES
        # DRAW BRUSH FACES
        # DISP ONLY
        # DISP FACES AS DISP + SOLID FACES AS SOLID
        # DRAW WALKABLE (calculate tri normals)
        self.displacements = {}
        for i, side in enumerate(string_solid):
            if hasattr(solid, 'dispinfo'):
                self.displacements[i] = solid.dispinfo

        self.disp_tris = {} # {side_index: [vertex, ...], ...}        

    def flip(self, center, axis):
        """axis is a vector"""
        # flip along axis
        # maintain outward facing plane normals
        # invert all plane normals along axis, flip along axis
        ...

    def recalculate(self):
        """update self.string_solid to match vertices"""
        # foreach face
        #   solid.sides.append(vmf_tool.namespace(...))
        #   solid.sides.[-1].plane = '({:.f}) ({:.f}) ({:.f})'.format(*face[:3])
        ...

    def rotate(self, pivot_point=None):
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
