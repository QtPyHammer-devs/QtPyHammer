import math

from QtPyHammer.utilities import vector


class TestVec2:
    a = vector.vec2(1, 2)
    b = vector.vec2(3, 4)  # pythagorean triple with 5

    def test_abs(self):
        assert abs(self.b) == 5

    def test_addition(self):
        assert self.a + self.b == vector.vec2(4, 6)
        assert self.b - self.a == vector.vec2(2, 2)  # __sub__

    def test_equality_checks(self):
        assert self.a == vector.vec2(1, 2)
        assert self.a == [1, 2]
        assert self.b == (3, 4)
        assert self.b == 5  # magnitude == float

    def test_format(self):
        assert repr(self.a) == "[1, 2]"
        assert f"{self.b}" == "3 4"
        pie = vector.vec2(3.14159, 2.71828)
        assert f"{pie:.4}" == "3.142 2.718"

    def test_floor_division(self):
        assert vector.vec2(5, 6) // 2 == vector.vec2(2, 3)

    def test_getitem(self):
        assert self.a[0] == self.a.x
        assert self.b[-1] == self.b.y

    def test_iter(self):
        expected = (1, 2)
        for value, correct_value in zip(self.a, expected):
            assert value == correct_value

    def test_len(self):
        assert len(self.a) == 2  # length of iterable form

    def test_multiplication(self):
        assert self.a * 2 == vector.vec2(2, 4)
        assert 3 * self.b == vector.vec2(9, 12)  # __rmul__

    def test_negativity(self):
        assert -self.b == vector.vec2(-3, -4)

    def test_magnitude(self):
        assert self.a.magnitude() == math.sqrt(5)


class TestVec3:
    a = vector.vec3(1, 4, 5)
    b = vector.vec3(2, 3, 6)  # pythagorean quadruple with 7

    def test_abs(self):
        assert abs(self.b) == 7

    def test_addition(self):
        assert self.a + self.b == vector.vec3(3, 7, 11)
        assert self.b - self.a == vector.vec3(1, -1, 1)  # __sub__

    def test_equality_checks(self):
        assert self.a == vector.vec3(1, 4, 5)
        assert self.a == [1, 4, 5]
        assert self.b == (2, 3, 6)
        assert self.b == 7  # magnitude == float

    def test_format(self):
        assert repr(self.a) == "[1, 4, 5]"
        assert f"{self.b}" == "2 3 6"
        phipie = vector.vec3(1.61803, 3.14159, 2.71828)
        assert f"{phipie:.4}" == "1.618 3.142 2.718"

    def test_floor_division(self):
        assert vector.vec3(5, 6, 9) // 2 == vector.vec3(2, 3, 4)

    def test_getitem(self):
        assert self.a[0] == self.a.x
        assert self.a[-1] == self.a.z

    def test_iter(self):
        expected = (1, 4, 5)
        for value, correct_value in zip(self.a, expected):
            assert value == correct_value

    def test_len(self):
        assert len(self.a) == 3  # length of iterable form

    def test_multiplication(self):
        assert self.a * 2 == vector.vec3(2, 8, 10)
        assert 3 * self.b == vector.vec3(6, 9, 18)  # __rmul__
        # assert vec3 multiplication

    def test_negativity(self):
        assert -self.b == vector.vec3(-2, -3, -6)

    def test_magnitude(self):
        assert self.a.magnitude() == math.sqrt(42)
