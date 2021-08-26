from QtPyHammer.utilities.physics import AxisAlignedBoundingBox
from QtPyHammer.utilities import vector


class TestAxisAlignedBoundingBox:
    def test_merge(self):
        aabb1 = AxisAlignedBoundingBox((0, 0, 0), (1, 1, 1))
        aabb2 = AxisAlignedBoundingBox((-1, -1, -1), (2, 2, 2))
        assert aabb1 + aabb2 == AxisAlignedBoundingBox((-1, -1, -1), (2, 2, 2))

    def test_move(self):
        aabb = AxisAlignedBoundingBox((-.5, -.5, 0), (0.5, 0.5, 2))
        result = AxisAlignedBoundingBox((-.5, -.5, 1), (0.5, 0.5, 3))
        assert aabb + vector.vec3(0, 0, 1) == result
