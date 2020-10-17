import unittest

from QtPyHammer.utilities import vector
from QtPyHammer.utilities.physics import aabb


class TestAABBMethods(unittest.TestCase):

    def test_Adding_AABBs(self):
        aabb1 = aabb((0, 0, 0), (1, 1, 1))
        aabb2 = aabb((-1, -1, -1), (2, 2, 2))
        self.assertEqual(aabb1 + aabb2, aabb((-1, -1, -1), (2, 2, 2)))

    def test_AABB_plus_Position(self):
        aabb1 = aabb((-.5, -.5, 0), (0.5, 0.5, 2))
        aabb_result = aabb((-.5, -.5, 1), (0.5, 0.5, 3))
        self.assertEqual(aabb1 + vector.vec3(0, 0, 1), aabb_result)
