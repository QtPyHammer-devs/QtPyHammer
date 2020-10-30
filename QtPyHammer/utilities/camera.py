"""Classes for creating and using cameras in 3D"""
import OpenGL.GL as gl

from . import vector

FORWARD = 0x00
BACK = 0x01
LEFT = 0x02
RIGHT = 0x03
UP = 0x04
DOWN = 0x05

keybinds = {FORWARD: [], BACK: [],
            LEFT: [], RIGHT: [],
            UP: [], DOWN: []}

sensitivity = 2


def clamp(value, minimum, maximum):
    """clamp range of rotation to avoid gimball lock"""
    if minimum <= value <= maximum:
        return value
    elif minimum > value:
        return minimum
    elif maximum < value:
        return maximum


class freecam:
    """Quake / Source free motion camera"""
    __slots__ = ["position", "rotation", "speed"]

    def __init__(self, position, rotation, speed=0.75):
        self.position = vector.vec3(*position)
        self.rotation = vector.vec3(*rotation)
        self.speed = speed

    def update(self, mousepos, keys, dt):
        """Take inputs and move at self.speed"""
        # MOUSE
        global sensitivity
        self.rotation.z += mousepos.x * sensitivity
        self.rotation.x += mousepos.y * sensitivity
        self.rotation.x = clamp(self.rotation.x, -90, 90)
        # KEYBOARD
        local_move = vector.vec3()

        def pressed(direction):
            return any((k in keys) for k in keybinds[direction])

        local_move.x = -(pressed(LEFT) - pressed(RIGHT))
        local_move.y = -(pressed(BACK) - pressed(FORWARD))
        local_move.z = -(pressed(DOWN) - pressed(UP))
        global_move = local_move.rotate(*-self.rotation)
        self.position += global_move * self.speed * dt

    def set(self):
        gl.glRotate(-90, 1, 0, 0)  # make Y+ forward
        gl.glRotate(self.rotation.x, 1, 0, 0)
        gl.glRotate(self.rotation.z, 0, 0, 1)
        gl.glTranslate(*-self.position)

    def __repr__(self):
        pos = [round(x, 2) for x in self.last_position]
        pos_string = str(pos)
        rot = [round(x, 2) for x in self.rotation]
        rot_string = str(rot)
        v = round(self.speed, 2)
        v_string = str(v)
        return "  ".join([pos_string, rot_string, v_string])


class firstperson:
    """First-person camera"""
    __slots__ = ["rotation"]

    def __init__(self, rotation=(0, 0, 0)):
        self.rotation = vector.vec3(*rotation)

    def update(self, mouse):
        global sensitivity
        self.rotation.z += mouse.x * sensitivity
        self.rotation.x += mouse.y * sensitivity

    def set(self, position):
        gl.glRotate(self.rotation.x - 90, 1, 0, 0)
        gl.glRotate(self.rotation.z, 0, 0, 1)
        gl.glTranslate(-position.x, -position.y, -position.z)


class thirdperson:
    """Third-person Camera"""
    __slots__ = ["position", "rotation", "radius", "offset"]

    def __init__(self, position, rotation, radius, offset=(0, 0)):
        self.position = vector.vec3(*position)
        self.rotation = vector.vec3(*rotation)
        self.radius = radius
        self.offset = vector.vec2(offset)

    def update(self):
        """write your own implementation"""
        raise NotImplementedError("thirdperson is a baseclass, write your own update function")

    def set(self):
        gl.glRotate(self.rotation.x, 1, 0, 0)
        gl.glRotate(self.rotation.y, 0, 1, 0)
        gl.glRotate(self.rotation.z, 0, 0, 1)
        gl.glTranslate(-self.position.x, -self.position.y, -self.position.z)
        gl.glTranslate(0, 0, -self.radius)
        gl.glTranslate(self.offset.x, self.offset.y, 0)
