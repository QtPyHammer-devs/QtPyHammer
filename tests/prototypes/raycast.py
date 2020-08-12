﻿import ctypes
import math
import re
import time

from OpenGL.GL import *
from OpenGL.GLU import *
from sdl2 import *


class vector:
    def __init__(self, x=0, y=0, z=0):
        self.x = x
        self.y = y
        self.z = z

    def __add__(self, other):
        return vector(*[a + b for a, b in zip(self, other)])

    def __iter__(self):
        return iter((self.x, self.y, self.z))

    def __mul__(self, other):
        if not isinstance(other, (int, float)):
            raise NotImplementedError()
        return vector(*[a * other for a in self])

    def __neg__(self):
        return vector(*[-a for a in self])

    def __repr__(self):
        return f"vector({self.x}, {self.y}, {self.z})"


# CONTROLS:
# LEFT MOUSE - cast ray
# RIGHT MOUSE - rotate camera
# O - orthographic projection
# P - perspective projection
def main(width, height):
    SDL_Init(SDL_INIT_VIDEO)
    window = SDL_CreateWindow(b"SDL2 OpenGL", SDL_WINDOWPOS_CENTERED,  SDL_WINDOWPOS_CENTERED, width, height, SDL_WINDOW_OPENGL | SDL_WINDOW_BORDERLESS)
    glContext = SDL_GL_CreateContext(window)
    SDL_GL_SetSwapInterval(0)
    glClearColor(0, 0, 0, 0)
    glEnable(GL_DEPTH_TEST)
    aspect_ratio = width / height
    fov = 90
    gluPerspective(fov, aspect_ratio, 0.001, 1024)
##    glOrtho(-2 * aspect_ratio, 2 * aspect_ratio, -2, 2, 0.001, 1024)
    glTranslate(0, 0, -2)
    glPointSize(4)

    ray_origin = vector(0, 0, 2)
    ray_direction = vector(0, 0, 1)

    x_offset, y_offset = vector(), vector()
    fov_scalar = 1

    mouse = vector(0, 0)
    dragging = False
    camera_moving = False
    ortho_mode = False

    def reset_view():
        glLoadIdentity()
        if ortho_mode:
            glOrtho(-2 * aspect_ratio, 2 * aspect_ratio, -2, 2, 0.001, 1024)
        else:
            gluPerspective(fov, aspect_ratio, 0.001, 1024)
        glTranslate(0, 0, -2)
    
    tickrate = 1 / 0.015
    tick_number = 0
    old_time = time.time()
    event = SDL_Event()
    while True:
        while SDL_PollEvent(ctypes.byref(event)) != 0:
            if event.type == SDL_QUIT or event.key.keysym.sym == SDLK_ESCAPE and event.type == SDL_KEYDOWN:
                SDL_GL_DeleteContext(glContext)
                SDL_DestroyWindow(window)
                SDL_Quit()
                return False
            elif event.type == SDL_MOUSEMOTION:
                mouse = vector(event.motion.x, event.motion.y)
                if camera_moving:
                    glRotate(5, -event.motion.yrel, event.motion.xrel, 0)
            elif event.type == SDL_MOUSEBUTTONDOWN:
                if event.button.button == SDL_BUTTON_LEFT:
                    dragging = True
                elif event.button.button == SDL_BUTTON_RIGHT:
                    camera_moving = True
            elif event.type == SDL_MOUSEBUTTONUP:
                if event.button.button == SDL_BUTTON_LEFT:
                    dragging = False
                    print(f"{fov = }")
                    print(f"{fov_scalar = }")
                    print(f"ray released @ {mouse.x} {mouse.y}")
                    print(f"{ray_origin = }")
                    print(f"{ray_direction = }")
                    print()
                elif event.button.button == SDL_BUTTON_RIGHT:
                    camera_moving = False
                    reset_view()
            elif event.type == SDL_KEYUP:
                key = event.key.keysym.sym
                if key in (SDLK_o, SDLK_p):
                    ortho_mode = True if key == SDLK_o else False
                    reset_view()
                elif key == SDLK_UP:
                    fov += 1
                    reset_view()
                elif key == SDLK_DOWN:
                    fov -= 1
                    reset_view()

        dt = time.time() - old_time
        while dt >= 1 / tickrate:
            if dragging:
                # CALCULATE RAY
                camera_position = vector(0, 0, 2)
                camera_forward = vector(0, 0, -1)
                camera_up = vector(0, 1, 0)
                camera_right = vector(1, 0, 0)
                x_offset = camera_right * ((mouse.x * 2 - width) / width)
                x_offset *= aspect_ratio
                y_offset = -camera_up * ((mouse.y * 2 - height) / height)
                fov_scalar = math.tan(math.radians(fov / 2))
                x_offset *= fov_scalar
                y_offset *= fov_scalar
                ray_direction = camera_forward + x_offset + y_offset
                ray_direction *= 768
            dt -= 1 / tickrate
            old_time = time.time()
            
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        glBegin(GL_LINES)
        glColor(1, 1, 1)
        glVertex(*ray_origin)
        glVertex(*(ray_origin + ray_direction))
        glColor(1, 0, 0)
        glVertex(0, 0, 0)
        glVertex(1, 0, 0)
        glColor(0, 1, 0)
        glVertex(0, 0, 0)
        glVertex(0, 1, 0)
        glColor(0, 0, 1)
        glVertex(0, 0, 0)
        glVertex(0, 0, 1)
        glEnd()

        glBegin(GL_POINTS)
        glColor(1, 1, 1)
        glVertex(*ray_origin)
        glVertex(*(ray_origin + ray_direction))
        glColor(1, 0, 1)
        glVertex(x_offset.x, y_offset.y)
        glEnd()

        glBegin(GL_QUADS)
        glColor(1, 0.5, 0.25)
        glVertex(1, 1, 2.001)
        glVertex(1, -1, 2.001)
        glVertex(-1, -1, 2.001)
        glVertex(-1, 1, 2.001)
        glEnd()
        
        SDL_GL_SwapWindow(window)
        


if __name__ == '__main__':
    import getopt
    import sys
    options = getopt.getopt(sys.argv[1:], 'w:h:')
    width = 640
    height = 480
    for option in options:
        for key, value in option:
            if key == '-w':
                width = int(value)
            elif key == '-h':
                height = int(value)
    main(width, height)
