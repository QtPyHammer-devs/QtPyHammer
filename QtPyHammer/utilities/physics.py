from __future__ import annotations
from typing import Union

from . import vector


class Plane:
    normal: vector.vec3
    distance: float

    def __init__(self, normal: vector.vec3, distance: float):
        self.normal = vector.vec3(*normal)
        self.distance = distance

    def __neg__(self):
        return Plane(-self.normal, self.distance)

    def flip(self):
        """Mutates self to face the opposite direction"""
        self.normal = -self.normal
        self.distance = -self.distance


class AxisAlignedBoundingBox:
    mins: vector.vec3
    maxs: vector.vec3

    def __init__(self, mins: vector.vec3, maxs: vector.vec3):
        self.mins = vector.vec3(*mins)
        self.maxs = vector.vec3(*maxs)

    def __add__(self, other: Union[AxisAlignedBoundingBox, vector.vec3]) -> AxisAlignedBoundingBox:
        """Merge bounds with AABB or translate by Vec3"""
        if isinstance(other, AxisAlignedBoundingBox):
            # merge bounds with other AABB [AABB tree node == sum(node.children)]
            min_x = min(self.mins.x, other.mins.x)
            max_x = max(self.maxs.x, other.maxs.x)
            min_y = min(self.mins.y, other.mins.y)
            max_y = max(self.maxs.y, other.maxs.y)
            min_z = min(self.mins.z, other.mins.z)
            max_z = max(self.maxs.z, other.maxs.z)
            return AxisAlignedBoundingBox((min_x, min_y, min_z), (max_x, max_y, max_z))
        elif isinstance(other, vector.vec3):
            # translate by vector
            return AxisAlignedBoundingBox(self.mins + other, self.maxs + other)

    def __eq__(self, other):
        if not isinstance(other, AxisAlignedBoundingBox):
            return False
        if (self.mins == other.mins) and (self.maxs == other.maxs):
            return True
        else:
            return False

    # NOTE: why? is this really helpful?
    def __getitem__(self, index):
        return [self.mins, self.maxs][index]

    def __iter__(self):
        return iter([self.mins, self.maxs])  # would zipping be better?
    # TODO: check if __getitem__ & __iter__ are used, and if they could be used better
    # - a good use case should be: intuitive, helpful, performant, simple

    def __repr__(self):
        return f"{self.__class__.__name__}(mins={self.mins}, maxs={self.maxs})"

    # NOTE: not very clear, is this even used?
    # definitely needs a test
    def intersects(self, other: AxisAlignedBoundingBox) -> bool:
        if not isinstance(other, AxisAlignedBoundingBox):
            raise RuntimeError(f"{other.__name__} is not an AxisAlignedBoundingBox")
        if any([not ((self.min[a] < other.max[a]) and (self.max[a] > other.min[a])) for a in range(3)]):
            return False
        else:
            return True

    def contains(self, other: Union[AxisAlignedBoundingBox, vector.vec3]) -> bool:
        if isinstance(other, AxisAlignedBoundingBox):
            if any([not ((self.min[i] < other.min[i]) and (self.max[i] > other.max[i])) for i in range(3)]):
                return False
            else:
                return True
        elif isinstance(other, vector.vec3):
            if any([not (self.min[i] < other[i] < self.max[i]) for i in range(3)]):
                return False
            else:
                return True
        else:
            raise TypeError(f"Cannot determine how {type(self)} would contain {type(other)}")

    def depth_along_axis(self, axis: vector.vec3) -> float:
        depth = list(self.max - self.min)
        for i in range(3):
            depth[i] *= axis[i]
        depth = vector.vec3(*depth)
        return depth.magnitude()

    def cull_ray(self, ray: vector.vec3) -> vector.vec3:
        """Takes a ray and clips it to fit inside AxisAlignedBoundingBox"""
        out = list(self.max - self.min)
        for i in range(3):
            out[i] *= ray[i]
        return vector.vec3(*out)

    def verts(self) -> vector.vec3:  # generator
        """Generates out the corners via a 3-bit counter"""
        x = (self.mins.x, self.maxs.x)
        y = (self.mins.y, self.maxs.y)
        z = (self.mins.z, self.maxs.z)
        for i in range(8):
            yield vector.vec3(x[i & 4 >> 2], y[i & 2 >> 1], z[i & 1])
