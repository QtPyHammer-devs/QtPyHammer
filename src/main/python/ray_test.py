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

camera.sensitivity = 1
    
#TODO: Unlock camera with a keypress (toggle)
#TODO: Cast off-center ray (GL function to warp ray by projection matrix)

# for new solid_tool
# series of functions for assembling <class 'brush'> objects
# -- from model
# -- from string (.vmf segment)
# -- from series of planes (link to clipping tool)
# -- from 3D paint strokes
# -- from cloud of points
# parametric generators (USEFUL regular shapes)
# if no params given (texvec, material), generate them
def block_planes(bounds_min, bounds_max):
    planes = []
    for i in range(3): # generates a cube to fit bounds
        normal = vector.vec3(0, 0, 0)
        normal[i] = -1
        planes.append((normal, -bounds_min[i]))
        normal = vector.vec3(0, 0, 0)
        normal[i] = 1
        planes.append((normal, bounds_max[i]))
    return planes

def spike_planes(): # radius (internal), sides
    P0 = (vector.vec3(0, 0, -1), 0)
    planes = [P0]
    # degrees = 360 / sides
    planes.append((P0[0].rotate(y=135), 128))
    planes.append((planes[1][0].rotate(z=120), 128))
    planes.append((planes[1][0].rotate(z=-120), 128))
    planes.append((vector.vec3(0, 0, 1), 128))
    return planes

class brush:
    def __init__(self, planes):
        self.planes = planes

        self.dots = dict()
        self.crosses = dict()
        self.coincident_planes = [set() for i in self.planes]
        for i, plane in enumerate(self.planes):
            normal, distance = plane
            for j in range(i + 1, len(self.planes)): # compare pairs only once
                other_normal, other_distance = self.planes[j]
                parallelity = vector.dot(normal, other_normal)
                if abs(parallelity) != 1:
                    self.coincident_planes[i].add(j)
                    self.coincident_planes[j].add(i)
                self.dots[(i, j)] = parallelity
                self.crosses[(i, j)] = normal * other_normal

        self.triples = []
        for plane1, coincidents in enumerate(self.coincident_planes):
            for plane2 in coincidents:
                # skip repeats in here to go a little bit faster
                for plane3 in coincidents.intersection(self.coincident_planes[plane2]):
                    triple = set((plane1, plane2, plane3))
                    if triple not in self.triples:
                        self.triples.append(triple)
        # sum(index in t for t in self.triples) # number of points on plane face
        # sum({index1, index2}.issubset(t) for t in self.triples) # number of points on plane edge

        tv_map = dict()
        self.vertices = []
        self.face_indices = {i: [] for i, plane in enumerate(self.planes)}
        for triple in self.triples:
            try:
                point = intersect.planes_coincident_point(*[self.planes[i] for i in triple])
            except ZeroDivisionError as exc:
                A, B, C = (self.planes[i][0] for i in triple)
                print(f'{A:.3f} dot ({B:.3f} cross {C:.3f})')
                print(f'{A:.3f} dot {B * C:.3f}')
                print(f'{vector.dot(A, B * C):.3f}')
                print(f'{triple} does not meet at a point')
                continue
            cullers = set()
            for plane in triple:
                cullers = cullers.union(set(self.coincident_planes[plane]))
            cullers = cullers.difference(triple)
            for culler in cullers:
                normal, distance = self.planes[culler]
##                if vector.dot(point, normal) > distance:
##                    print(f'skipping {point:.3f}')
##                    continue
            if point not in self.vertices:
                print(f'adding {point:.3f} {triple}')
                self.vertices.append(point)
                tv_map[tuple(point)] = triple
            else:
                print(f'{point:.3f} {triple} repeat of {tv_map[tuple(point)]}')
            for plane_index in triple:
                self.face_indices[plane_index].append(self.vertices.index(point))

        for face, indices in self.face_indices.items():
            face_vertices = tuple(self.vertices[i] for i in indices)
            plane_normal = self.planes[face][0]
            sorted_vertices = vector.sort_clockwise(face_vertices, plane_normal)
            self.face_indices[face] = tuple(self.vertices.index(v) for v in sorted_vertices)

        # calc from tv_map (triples)
        # should be faster & easier
        self.edges = [] # wireframe
        for edge_loop in self.face_indices.values():
            for A, B in zip(edge_loop, (*edge_loop[1:], edge_loop[0])):
                if {A, B} not in self.edges:
                    self.edges.append({A, B})


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
    glEnable(GL_BLEND)
    glBlendFunc(GL_ONE, GL_ONE_MINUS_SRC_ALPHA)
    glPointSize(8)

    CAMERA = camera.freecam((160, -160, 245), (20, 0, -45), 192)
    mousepos = vector.vec2()
    
    rendered_ray = []
    intersection = (0, 0, 0)

    triangle = ((-128, 256, 0), (0, 384, 0), (128, 256, 0))
    triangle = tuple(map(vector.vec3, triangle))
    ray_intersects_triangle = False

##    test_brush = brush(block_planes((-64, -64, 64), (64, 64, 192)))
    test_brush = brush(spike_planes())

    keys = []

    locked_mouse = False
    SDL_SetRelativeMouseMode(SDL_TRUE)
    SDL_CaptureMouse(SDL_TRUE)
            
    tickrate = 1 / 0.015
    old_time = time.time()
    event = SDL_Event()
    while True:
        while SDL_PollEvent(ctypes.byref(event)) != 0:
            if event.type == SDL_QUIT or event.key.keysym.sym == SDLK_ESCAPE and event.type == SDL_KEYDOWN:
                SDL_GL_DeleteContext(glContext)
                SDL_DestroyWindow(window)
                SDL_Quit()
                return test_brush
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
                mousepos = vector.vec2(event.motion.xrel, event.motion.yrel)
                SDL_WarpMouseInWindow(window, width // 2, height // 2)
            if event.type == SDL_MOUSEWHEEL:
                if CAMERA.speed + event.wheel.y * 32 > 0: # speed limits
                    CAMERA.speed += event.wheel.y * 32

        dt = time.time() - old_time
        while dt >= 1 / tickrate:
            # KEYTIME to prevent repeats
            CAMERA.update(mousepos, keys, 1 / tickrate)
            mousepos = vector.vec2(0, 0)
            if SDLK_z in keys:
                SDL_SetRelativeMouseMode(SDL_FALSE if locked_mouse else SDL_TRUE)
                locked_mouse = not locked_mouse
            if SDLK_r in keys:
                CAMERA = camera.freecam(None, None, 128)
            if SDLK_BACKQUOTE in keys:
                print(f'VERTICES: {test_brush.vertices}')
            if SDL_BUTTON_LEFT in keys:
                ray_start = CAMERA.position
                ray_dir = vector.vec3(0, 1, 0).rotate(*-CAMERA.rotation)
                rendered_ray = [ray_start, ray_start + (ray_dir * 4096)]
                ray_intersects_triangle, intersection = intersect.ray_triangle((ray_start, ray_dir), triangle)

                # test against brush
                brush_ray_intersections = intersect.ray_hull((ray_start, ray_dir), test_brush.planes)
                if len(brush_ray_intersections) != 0:
                    print(brush_ray_intersections)
                    ray_intersects_brush = True
                    intersection = ray_start + ray_dir * brush_ray_intersections[0]
                
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
        glColor(*((0, 1, .5) if ray_intersects_triangle else (1, .5, 0)))

        # RAY
        glBegin(GL_LINES)
        for point in rendered_ray:
            glVertex(*point)
        glEnd()

        # POINT OF INTERSECTION
        if ray_intersects_triangle:
            glBegin(GL_POINTS)
            glVertex(*intersection)
            glEnd()

        # TRIANGLE
        glLineWidth(2)
        glBegin(GL_LINES)
        for vertex, next_vertex in zip(triangle, list(triangle[1:]) + [triangle[0]]):
            glVertex(*vertex)
            glVertex(*next_vertex)
        glEnd()
        glColor(*((0, .5, .25, .5) if ray_intersects_triangle else (.5, .25, 0, .5)))
        glBegin(GL_TRIANGLES)
        for vertex in triangle:
            glVertex(*vertex)
        glEnd()

        # BRUSH
        colour = (0.5, 0.25, 0)
        for face, indices in test_brush.face_indices.items():
            glColor(*colour, 0.5)
            colour = (*colour[1:], colour[0])
            glBegin(GL_POLYGON)
            for index in indices:
                glVertex(*test_brush.vertices[index])
            glEnd()

        # BRUSH WIREFRAME
        glColor(1, .5, 0)
        glBegin(GL_LINES)
        for edge in test_brush.edges:
            for index in edge:
                glVertex(*test_brush.vertices[index])
        glEnd()

        glColor(1, .5, 0)
        glBegin(GL_POINTS)
        for vertex in test_brush.vertices:
            glVertex(*vertex)
        # PLANE CENTERS
        glColor(1, 0, 1)
        for normal, distance in test_brush.planes:
            glVertex(*(normal * distance))
        glEnd()

        glLineWidth(1)
        glColor(1, 0, 1)
        glBegin(GL_LINES)
        for normal, distance in test_brush.planes:
            glVertex(*(normal * distance))
            glVertex(*(normal * distance + normal * 32))
        glEnd()

        glEnable(GL_DEPTH_TEST)

        glPopMatrix()
        SDL_GL_SwapWindow(window)

if __name__ == '__main__':
    try:
        output = main()
    except Exception as exc:
        SDL_Quit()
        raise exc
