import itertools
import re

from . import vector, vmf


def triangle_of(string):
    """"'(X Y Z) (X Y Z) (X Y Z)' --> (vec3(X, Y, Z), vec3(X, Y, Z), vec3(X, Y, Z))"""
    points = re.findall("(?<=\().+?(?=\))", string)
    vector_of = lambda P: vector.vec3(map(float, P.split(" ")))
    return tuple(map(vector_of, points))

def plane_of(A, B, C):
    """returns the plane (vec3 normal, float distance) the triangle ABC represents"""
    normal = ((A - B) * (C - B)).normalise()
    return (normal, vector.dot(normal, A))


class texture_vector: # pairing uaxis and vaxis together would be nice
    def __init__(self, string):
        """'[X Y Z Offset] Scale' --> self.vector, self.offset, self.scale"""
        x, y, z, offset = re.findall("(?<=[\[\ ]).+?(?=[\ \]])", string)
        self.vector = x, y, z
        self.offset = offset
        self.scale = re.search("(?<=\ )[^\ ]*$", side.uaxis).group(0)

    def linear_pos(self, position):
        """half a uv, need 2 texture_vectors for the full uv"""
        return (vector.dot(position, self.vector) + self.offset) / self.scale

    def align_to_normal(self, normal):
        raise NotImplementedError()
    
    # & a wrapping method for alt+right click


class side:
    def __init__(self, namespace):
        self.id = int(namespace.id)
        self.base_triangle = triangle_of(namespace.plane)
        self.plane = plane_of(*self._triangle) # vec3 normal, float distance
        self.material = namespace.material
        self.uaxis = texture_vector(namespace.uaxis)
        self.vaxis = texture_vector(namespace.vaxis)
        self.rotation = float(namespace.rotation)
        self.lightmap_scale = int(namespace.lightmapscale)
        self.smoothing_groups = int(namespace.smoothing_groups)

        self.face = [] # calculated by clipping against other planes in solid.__init__

    def uv_at(self, position):
        u = self.uaxis.linear_pos(position)
        v = self.vaxis.linear_pos(position)
        return (u, v)


class solid:
    __slots__ = ("colour", "id", "is_displacement", "sides", "side_ids", "source")

    def __init__(self, namespace): # takes a namespace solid (imported from a .vmf)
        """Initialise from namespace (vmf import)"""
        self.source = namespace # preserved for debugging
        self.id = int(self.source.id)
        self.colour = tuple(int(x) / 255 for x in solid_namespace.editor.color.split())

        self.sides = [side(s) for s in self.source.sides]
        self.side_ids = [s.id for s in self.sides]
        # ^ for looking up sides by id
        if any([hasattr(s, "disp_info") for s in self.sides]):
            self.is_displacement = True
        else:
            self.is_displacement = False
        
        for i, side in enumerate(self.sides):
            normal, distance = side.plane
            if abs(normal.z) != 1:
                non_parallel = vector.vec3(z=-1)
            else:
                non_parallel = vector.vec3(y=-1)
            local_y = (non_parallel * normal).normalise()
            local_x = (local_y * normal).normalise()
            center = sum(side.base_triangle, vector.vec3()) / 3
            # ^ centered on string triangle, but rounding errors abound
            # however, using vector.vec3 does mean math.fsum is utilitsed
            radius = 10 ** 4 # should be larger than any reasonable brush
            ngon = [center + ((-local_x + local_y) * radius),
                             center + ((local_x + local_y) * radius),
                             center + ((local_x + -local_y) * radius),
                             center + ((-local_x + -local_y) * radius)]
            for other_plane in self.planes:
                if other_plane == plane or plane[0] == -other_plane[0]:
                    continue
                ngon, offcut = clip(ngon, other_plane).values() # back, front
            self.sides[i].face = ngon
            # if this side is a displacement:
            # -- check ngon is a quad
            # -- log an error if it isn't
        

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
    return split_verts
