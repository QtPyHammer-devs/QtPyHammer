"""Classes for creating and using cameras in 3D"""
from OpenGL.GL import *
from OpenGL.GLU import *

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


class freecam:
    """Quake / Source free motion camera"""
    __slots__ = ["position", "rotation", "speed"]

    def __init__(self, position, rotation, speed=0.75):
        self.position = vector.vec3(position) if position is not None else vector.vec3()
        # self.next_position = self.last_position
        self.rotation = vector.vec3(rotation) if rotation is not None else vector.vec3()
        self.speed = speed

    def update(self, mousepos, keys, dt):
        """Take inputs and move at self.speed"""
        # MOUSE
        global sensitivity
        self.rotation.z += mousepos.x * sensitivity
        self.rotation.x += mousepos.y * sensitivity
        clamp = clamp = lambda v, m, M: m if v < m else M if v > M else v
        self.rotation.x = clamp(self.rotation.x, -90, 90)
        # ^ clamping to avoid gimball lock
        # KEYBOARD
        # self.last_position = self.next_position
        local_move = vector.vec3()

        def pressed(direction):
            return any((k in keys) for k in keybinds[direction])

        local_move.x = -(pressed(LEFT) - pressed(RIGHT))
        local_move.y = -(pressed(BACK) - pressed(FORWARD))
        local_move.z = -(pressed(DOWN) - pressed(UP))
        global_move = local_move.rotate(*-self.rotation)
        self.position += global_move * self.speed * dt

    def set(self):
        glRotate(-90, 1, 0, 0)  # make Y+ forward
        glRotate(self.rotation.x, 1, 0, 0)
        glRotate(self.rotation.z, 0, 0, 1)
        # current_position = vector.lerp(self.last_position, self.next_position, lerp_factor)
        glTranslate(*-self.position)

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

    def __init__(self, rotation=None):
        self.rotation = vector.vec3(rotation) if rotation is not None else vector.vec3()

    def update(self, mouse):
        global sensitivity
        self.rotation.z += mouse.x * sensitivity
        self.rotation.x += mouse.y * sensitivity

    def set(self, position):
        glRotate(self.rotation.x - 90, 1, 0, 0)
        glRotate(self.rotation.z, 0, 0, 1)
        glTranslate(-position.x, -position.y, -position.z)


class thirdperson:
    """Third-person Camera"""
    __slots__ = ["position", "rotation", "radius", "offset"]

    def __init__(self, position, rotation, radius, offset=(0, 0)):
        self.position = vector.vec3(position)
        self.rotation = vector.vec3(rotation)
        self.radius = radius
        self.offset = vector.vec2(offset)

    def update(self):
        """write your own implementation"""
        pass

    def set(self):
        glRotate(self.rotation.x, 1, 0, 0)
        glRotate(self.rotation.y, 0, 1, 0)
        glRotate(self.rotation.z, 0, 0, 1)
        glTranslate(-self.position.x, -self.position.y, -self.position.z)
        glTranslate(0, 0, -self.radius)
        glTranslate(self.offset.x, self.offset.y, 0)
