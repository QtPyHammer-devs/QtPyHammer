import itertools
import re

from . import vector


def triangle_of(string):
    """"'(X Y Z) (X Y Z) (X Y Z)' --> (vec3(X, Y, Z), vec3(X, Y, Z), vec3(X, Y, Z))"""
    points = re.findall("(?<=\().+?(?=\))", string)
    vector_of = lambda P: vector.vec3(*map(float, P.split(" ")))
    return tuple(map(vector_of, points))

def plane_of(A, B, C):
    """returns the plane (vec3 normal, float distance) the triangle ABC represents"""
    normal = ((A - B) * (C - B)).normalise()
    return (normal, vector.dot(normal, A))


class texture_vector: # pairing uaxis and vaxis together would be nice
    def __init__(self, string):
        """'[X Y Z Offset] Scale' --> self.vector, self.offset, self.scale"""
        x, y, z, offset = re.findall("(?<=[\[\ ]).+?(?=[\ \]])", string)
        self.vector = tuple(map(float, [x, y, z]))
        self.offset = float(offset)
        self.scale = float(re.search("(?<=\ )[^\ ]+$", string).group(0))

    def linear_pos(self, position):
        """half a uv, need 2 texture_vectors for the full uv"""
        return (vector.dot(position, self.vector) + self.offset) / self.scale

    def align_to_normal(self, normal):
        raise NotImplementedError()
    
    # & a wrapping method for alt+right click


class face:
    def __init__(self, namespace):
        self.id = int(namespace.id)
        self.base_triangle = triangle_of(namespace.plane)
        self.plane = plane_of(*self.base_triangle) # vec3 normal, float distance
        self.material = namespace.material
        self.uaxis = texture_vector(namespace.uaxis)
        self.vaxis = texture_vector(namespace.vaxis)
        self.rotation = float(namespace.rotation)
        self.lightmap_scale = int(namespace.lightmapscale)
        self.smoothing_groups = int(namespace.smoothing_groups)

        self.polygon = []
        # ^ calculated by clipping against other planes in solid.__init__

        if hasattr(namespace, "dispinfo"):
            self.displacement = displacement(namespace.dispinfo)

    def uv_at(self, position):
        u = self.uaxis.linear_pos(position)
        v = self.vaxis.linear_pos(position)
        return (u, v)


class displacement:
    def __init__(self, namespace):
        self.power = int(namespace.power)
        self.start = tuple(map(float, re.findall("(?<=[\[\ ]).+?(?=[\ \]])", namespace.startposition)))
        # self.flags = int(namespace.flags)
        # self.elevation = int(namespace.elevation)
        # self.subdiv = int(subdiv)

        self.normals = []
        self.distances = []
        # self.offsets = []
        # self.offset_normals = []
        self.alphas = []
        # self.triangle_tags = []
        # self.allowed_verts = []
        floats = lambda s: tuple(map(float, s.split(" ")))
        row_count = (2 ** self.power) + 1
        for i in range(row_count):
            row = f"row{i}"
            row_strings = namespace.normals[row].split(" ")
            row_normals = []
            for i in range(row_count):
                i *= 3
                normal_string = " ".join(row_strings[i:i+3])
                row_normals.append(vector.vec3(floats(normal_string)))
            self.normals.append(row_normals)
            self.distances.append(floats(namespace.distances[row]))
            self.alphas.append(floats(namespace.alphas[row]))
            # almost always 0-255 (256 has been observed in the wild)
            # almost always an integer (however floats have also been seen)

    def change_power(self, new_power):
        """simplify / subdivide displacement further"""
        raise NotImplementedError()
        

class solid:
    __slots__ = ("colour", "id", "is_displacement", "faces", "face_ids", "source")

    def __init__(self, namespace):
        """Initialise from namespace (vmf import)"""
        self.source = namespace # preserved for debugging
        self.id = int(self.source.id)
        self.colour = tuple(int(x) / 255 for x in namespace.editor.color.split())

        global face
        self.faces = list(map(face, self.source.sides)) 
        self.face_ids = [f.id for f in self.faces]
        # ^ for lookup by id
        if any([hasattr(f, "displacement") for f in self.faces]):
            self.is_displacement = True
        else:
            self.is_displacement = False
        
        for i, f in enumerate(self.faces):
            normal, distance = f.plane
            if abs(normal.z) != 1:
                non_parallel = vector.vec3(z=-1)
            else:
                non_parallel = vector.vec3(y=-1)
            local_y = (non_parallel * normal).normalise()
            local_x = (local_y * normal).normalise()
            center = sum(f.base_triangle, vector.vec3()) / 3
            # ^ centered on string triangle, but rounding errors abound
            # however, using vector.vec3 does mean math.fsum is utilitsed
            radius = 10 ** 4 # should be larger than any reasonable brush
            ngon = [center + ((-local_x + local_y) * radius),
                             center + ((local_x + local_y) * radius),
                             center + ((local_x + -local_y) * radius),
                             center + ((-local_x + -local_y) * radius)]
            for other_f in self.faces:
                if other_f.plane == f.plane: # skip yourself
                    continue
                ngon, offcut = clip(ngon, other_f.plane).values()
            self.faces[i].polygon = ngon
            if hasattr(f, "displacement") and len(ngon) != 4:
                raise RuntimeError("{self.id} {f.id} invalid displacement")
        

    def __repr__(self):
        return f"<solid {len(self.vertices)} vertices>"

    def translate(self, offset):
        """offset is a vector"""
        raise NotImplementedError()


def clip(poly, plane):
    normal, distance = plane
    split_verts = {"back": [], "front": []} # allows for 3 cutting modes
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
            cut_point = [round(a, 2) for a in cut_point]
            # .vmf floating-point accuracy sucks
            split_verts["back"].append(cut_point)
            split_verts["front"].append(cut_point)
            # ^ won't one of these points be added twice?
    return split_verts
