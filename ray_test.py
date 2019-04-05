import ctypes
import enum
import intersect
import itertools
import numpy as np # for vertex buffers Numpy is needed (available through pip)
from OpenGL.GL import * # Installed via pip (PyOpenGl 3.1.0)
from OpenGL.GL.shaders import compileShader, compileProgram
from OpenGL.GLU import * # PyOpenGL-accelerate 3.1.0 requires MSVC 2015
# get precompiled binaries if you can, it's much less work
from sdl2 import * #Installed via pip (PySDL2 0.9.5)
# requires SDL2.dll (steam has a copy in it's main directory)
# and an Environment Variable (PYSDL2_DLL_PATH)
# PYSDL2_DLL_PATH must point to the folder containing the DLL
# this makes loading SDL2 addons with their DLLs in the same folders very easy
import time
import utilities.camera as camera
import utilities.vector as vector
    
#TODO: Unlock camera with a keypress (toggle)
#TODO: Cast off-center ray (GL function to warp ray by projection matrix)


def main(width=1024, height=576):
    SDL_Init(SDL_INIT_VIDEO)
    window = SDL_CreateWindow(b'SDL2 OpenGL', SDL_WINDOWPOS_CENTERED,  SDL_WINDOWPOS_CENTERED, width, height, SDL_WINDOW_OPENGL | SDL_WINDOW_BORDERLESS)
    glContext = SDL_GL_CreateContext(window)
    SDL_GL_SetSwapInterval(0)
    glClearColor(0.1, 0.1, 0.1, 0.0)
    glColor(1, 1, 1)
    gluPerspective(90, width / height, 0.1, 4096 * 4)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_CULL_FACE)
    glFrontFace(GL_CW)
    glPointSize(8)

    CAMERA = camera.freecam((160, -160, 160), None, 128)
    rendered_ray = []
    ray_intersects = False

    triangle = ((-128, 0, 0), (0, 128, 0), (128, 0, 0))
    triangle = tuple(map(vector.vec3, triangle))
    intersection = (0, 0, 0)

    SDL_SetRelativeMouseMode(SDL_TRUE)
    SDL_CaptureMouse(SDL_TRUE)

    mousepos = vector.vec2(-180, 120) # overrides start angle
    # need to move to an incremental camera so re-capturing the mouse doesn't
    #   reset the camera
    keys = []
            
    tickrate = 1 / 0.015
    old_time = time.time()
    event = SDL_Event()
    while True:
        while SDL_PollEvent(ctypes.byref(event)) != 0:
            if event.type == SDL_QUIT or event.key.keysym.sym == SDLK_ESCAPE and event.type == SDL_KEYDOWN:
                SDL_GL_DeleteContext(glContext)
                SDL_DestroyWindow(window)
                SDL_Quit()
                return False
            if event.type == SDL_KEYDOWN:
                if event.key.keysym.sym not in keys:
                    keys.append(event.key.keysym.sym)
            if event.type == SDL_KEYUP:
                while event.key.keysym.sym in keys:
                    keys.remove(event.key.keysym.sym)
            if event.type == SDL_MOUSEBUTTONDOWN:
                keys.append(event.button.button)
            if event.type == SDL_MOUSEBUTTONUP:
                while event.button.button in keys:
                    keys.remove(event.button.button)
            if event.type == SDL_MOUSEMOTION:
                mousepos += vector.vec2(event.motion.xrel, event.motion.yrel)
                SDL_WarpMouseInWindow(window, width // 2, height // 2)
            if event.type == SDL_MOUSEWHEEL:
                if CAMERA.speed + event.wheel.y * 32 > 0: # speed limits
                    CAMERA.speed += event.wheel.y * 32

        dt = time.time() - old_time
        while dt >= 1 / tickrate:
            CAMERA.update(mousepos, keys, 1 / tickrate)
            if SDLK_r in keys:
                CAMERA = camera.freecam(None, None, 128)
            if SDLK_BACKQUOTE in keys:
                print(f'RAY @ {ray_start:.3f} WITH DIR {ray_dir:.3f}')
                r = lambda x: f'({x:.2f})'
                print('INTERSECTS TRIANGLE', ', '.join(map(r, triangle)))
                print(f'@ {intersection:.3f}')
                        
            if SDL_BUTTON_LEFT in keys:
                ray_start = CAMERA.position
                ray_dir = vector.vec3(0, 1, 0).rotate(*-CAMERA.rotation)
                rendered_ray = [ray_start, ray_start + (ray_dir * 4096)]
                ray_intersects, intersection = intersect.ray_triangle((ray_start, ray_dir), triangle)
            dt -= 1 / tickrate
            old_time = time.time()

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glPushMatrix()
        CAMERA.set()
        
        # GRID
        glLineWidth(1)
        glColor(.25, .25, .25)
        glBegin(GL_LINES)
        for x in range(-32, 33):
            x = x * 64
            glVertex(x, -2048, 0)
            glVertex(x, 0, 0)
            glVertex(x, 0, 0)
            glVertex(x, 2048, 0)
        for y in range(-32, 33):
            y = y * 64
            glVertex(-2048, y, 0)
            glVertex(0, y, 0)
            glVertex(0, y, 0)
            glVertex(2048, y, 0)
        glEnd()

        # RAYCAST
        glDisable(GL_DEPTH_TEST)
        glColor(*((0, 1, .5) if ray_intersects else (1, .5, 0)))

        # RAY
        glBegin(GL_LINES)
        for point in rendered_ray:
            glVertex(*point)
        glEnd()

        # TRIANGLE
        glLineWidth(2)
        glBegin(GL_LINES)
        for vertex, next_vertex in zip(triangle, list(triangle[1:]) + [triangle[0]]):
            glVertex(*vertex)
            glVertex(*next_vertex)
        glEnd()

        # POINT OF INTERSECTION
        if ray_intersects:
            glBegin(GL_POINTS)
            glVertex(*intersection)
            glEnd()

        glEnable(GL_DEPTH_TEST)

        glPopMatrix()
        SDL_GL_SwapWindow(window)

if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        SDL_Quit()
        raise exc
