from . import vector


class plane:
    def __init__(self, normal, distance):
        self.normal = normal
        self.distance = distance

    def __neg__(self):
        return plane(-self.normal, self.distance)

    def flip(self):
        self.normal = -self.normal
        self.distance = -self.distance


class aabb:
    # use origin for octrees / bounding volume heirarchy?
    def __init__(self, mins, maxs):
        self.min = vector.vec3(*mins)
        self.max = vector.vec3(*maxs)

    def __add__(self, other):
        if isinstance(other, vector.vec3):
            return aabb(self.min + other, self.max + other)
        if isinstance(other, aabb):
            min_x = min(self.min.x, other.min.x)
            max_x = max(self.max.x, other.max.x)
            min_y = min(self.min.y, other.min.y)
            max_y = max(self.max.y, other.max.y)
            min_z = min(self.min.z, other.min.z)
            max_z = max(self.max.z, other.max.z)
            return aabb((min_x, min_y, min_z), (max_x, max_y, max_z))

    def __eq__(self, other):
        if isinstance(other, aabb):
            if self.min == other.min and self.max == other.max:
                return True
            return False
        return False

    def __getitem(self, index):
        return [self.min, self.max][index]

    def __iter__(self):
        return iter([self.min, self.max])

    def __repr__(self):
        extents = map(repr, [self.min, self.max])
        return ' '.join(extents)

    def intersects(self, other):
        if isinstance(other, aabb):
            if self.min.x < other.max.x and self.max.x > other.min.x:
                if self.min.y < other.max.y and self.max.y > other.min.y:
                    if self.min.z < other.max.z and self.max.z > other.min.z:
                        return True
            return False
        raise RuntimeError(other.__name__ + " is not an AABB")

    def contains(self, other):
        if isinstance(other, aabb):
            if self.min.x < other.min.x and self.max.x > other.max.x:
                if self.min.y < other.min.y and self.max.y > other.max.y:
                    if self.min.z < other.min.z and self.max.z > other.max.z:
                        return True
            return False
        elif isinstance(other, vector.vec3):
            if self.min.x < other.x < self.max.x:
                if self.min.y < other.y < self.max.y:
                    if self.min.z < other.z < self.max.z:
                        return True
            return False
        raise RuntimeError(other.__name__ + " is not an AABB")

    def depth_along_axis(self, axis):
        depth = list(self.max - self.min)
        for i in range(3):
            depth[i] *= axis[i]
        depth = vector.vec3(depth)
        return depth.magnitude()

    def cull_ray(self, ray):
        """takes a ray and clips it to fit inside aabb"""
        out = list(self.max - self.min)
        for i in range(3):
            out[i] *= ray[i]
        return vector.vec3(out)

    def verts(self):
        x = (self.min.x, self.max.x)
        y = (self.min.y, self.max.y)
        z = (self.min.z, self.max.z)
        for i in range(8):
            yield vector.vec3(x[i // 4 % 2], y[i // 2 % 2], z[i % 2])
