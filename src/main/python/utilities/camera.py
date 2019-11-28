"""Classes for creating and using cameras in 3D"""
import math
from OpenGL.GL import *
from OpenGL.GLU import *

from . import vector

keybinds = {'FORWARD': [], 'BACK': [], 'LEFT': [], 'RIGHT': [], 'UP': [], 'DOWN': []}
sensitivity = 0.25


class freecam:
    """Quake / Source free motion camera"""
    __slots__ = ['position', 'rotation', 'speed']

    def __init__(self, position, rotation, speed=0.75):
        self.position = vector.vec3(position) if position != None else vector.vec3()
        self.rotation = vector.vec3(rotation) if rotation != None else vector.vec3()
        self.speed = speed

    def update(self, mousepos, keys, dt):
        """Take inputs and move at self.speed"""
        global sensitivity
        self.rotation.z += mousepos.x * sensitivity # inverts when camera is upside-down
        self.rotation.x += mousepos.y * sensitivity
        # clamping the camera should stop control inversion
        # but free 360 degree rotation would be far more free
        # look up: gimball lock, quaternion rotation
        clamp = clamp = lambda v, m, M: m if v < m else M if v > M else v
        self.rotation.x = clamp(self.rotation.x, -120, 120) # 90 is restrictive and 180 is confusing
        # ^ remove these two lines for old camera behaviour ^

        local_move = vector.vec3()
        local_move.x = (any(k in keys for k in keybinds['RIGHT']) - any(k in keys for k in keybinds['LEFT'])) # may also invert
        local_move.y = (any(k in keys for k in keybinds['FORWARD']) - any(k in keys for k in keybinds['BACK']))
        local_move.z = (any(k in keys for k in keybinds['UP']) - any(k in keys for k in keybinds['DOWN']))
        global_move = local_move.rotate(*-self.rotation)
        self.position += global_move * self.speed * dt

    def set(self):
        glRotate(-90, 1, 0, 0)
        try:
            glRotate(self.rotation.x, 1, 0, 0)
        except Exception as exc:
            print(exc)
            print(self.rotation)
        glRotate(self.rotation.z, 0, 0, 1)
        glTranslate(-self.position.x, -self.position.y, -self.position.z)

    def __repr__(self):
        pos = [round(x, 2) for x in self.position]
        pos_string = str(pos)
        rot = [round(x, 2) for x in self.rotation]
        rot_string = str(rot)
        v = round(self.speed, 2)
        v_string = str(v)
        return '  '.join([pos_string, rot_string, v_string])


class firstperson:
    """First-person camera"""
    __slots__ = ['rotation']

    def __init__(self, rotation=None):
        self.rotation = vector.vec3(rotation) if rotation != None else vector.vec3()

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
    __slots__ = ['position', 'rotation', 'radius', 'offset']

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
