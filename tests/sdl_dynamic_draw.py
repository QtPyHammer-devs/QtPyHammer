import ctypes
import itertools
import math
import struct
import time

import numpy as np
from OpenGL.GL import *
from OpenGL.GL.shaders import compileShader, compileProgram
from OpenGL.GLU import *
from sdl2 import *


def main(width, height):
    SDL_Init(SDL_INIT_VIDEO)
    window = SDL_CreateWindow(b'SDL2 OpenGL', SDL_WINDOWPOS_CENTERED,  SDL_WINDOWPOS_CENTERED, width, height, SDL_WINDOW_OPENGL | SDL_WINDOW_BORDERLESS)
    glContext = SDL_GL_CreateContext(window)
    SDL_GL_SetSwapInterval(0)
    glClearColor(0.1, 0.1, 0.1, 0.0)
##    glOrtho(-2, 2, -2, 2, 0, 1024)
    # ^ left, right, bottom, top, near, far
    gluPerspective(90, 1, 0.1, 1024)
    # ^ fov, aspect, near, far
    glTranslate(0, 0, -2)
    
    glEnable(GL_DEPTH_TEST)
    glEnableClientState(GL_VERTEX_ARRAY)

    glPointSize(4)
    
    ###  BEGIN DYNAMIC DRAW BUFFER TEST  ###
    # VERTEX
    VERTEX_BUFFER = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, VERTEX_BUFFER)
    glBufferData(GL_ARRAY_BUFFER, 256, None, GL_DYNAMIC_DRAW)
    # ^ target, size, *data, usage
    
    cube_vertices = [(-1, 1, 1), (1, 1, 1), (1, -1, 1), (-1, -1, 1),
                     (-1, 1, -1), (1, 1, -1), (1, -1, -1), (-1, -1, -1)]
    cube_vertices = [*itertools.chain(*cube_vertices)]
    cube_vertices = np.array(cube_vertices, dtype=np.float32)
    glBufferSubData(GL_ARRAY_BUFFER, 0, len(cube_vertices) * 4, cube_vertices)
    # ^ target, start, length, *data

    # CHECK
    vertex_buffer_data = glGetBufferSubData(GL_ARRAY_BUFFER, 0, 8 * 3 * 4)
    # ^ target, start, length
    vertices = list(struct.iter_unpack("3f", vertex_buffer_data))
    print(vertices)

    # INDEX
    INDEX_BUFFER = glGenBuffers(1)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, INDEX_BUFFER)
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, 256, None, GL_DYNAMIC_DRAW)
    # ^ target, size, *data, usage

    cube_indices = [0, 1, 2, 3, 4, 5, 6, 7]
    cube_indices = np.array(cube_indices, dtype=np.uint32)
    glBufferSubData(GL_ARRAY_BUFFER, 0, len(cube_indices) * 4, cube_indices)
    # ^ target, start, length, *data

    # CHECK
    index_buffer_data = glGetBufferSubData(GL_ARRAY_BUFFER, 0, 8 * 4)
    # ^ target, start, length
    indices = [s[0] for s in struct.iter_unpack("I", index_buffer_data)]
    print(indices)
    ###  END DYNAMIC DRAW BUFFER TEST  ###

    vertex_shader_source = """#version 450 core
    layout(location = 0) in vec3 vertex_position;
    uniform mat4 gl_ModelViewProjectionMatrix;
    out vec3 position;
    
    void main()
    {
        position = vertex_position;

        gl_Position = gl_ModelViewProjectionMatrix * vec4(vertex_position, 1);
    }
    """
    vertex_shader = compileShader(vertex_shader_source, GL_VERTEX_SHADER)
    
    fragment_shader_source = """#version 450 core
    layout(location = 0) out vec4 outColour;
    in vec3 position;

    void main()
    {
        vec4 Ka = vec4(0.15, 0.15, 0.15, 1);
        outColour = vec4(.5, .5, .5, 1) + Ka;
    }
    """
    fragment_shader = compileShader(fragment_shader_source, GL_FRAGMENT_SHADER)

    shader_program = compileProgram(vertex_shader, fragment_shader)
    glLinkProgram(shader_program)
    glUseProgram(shader_program)

    glEnableVertexAttribArray(0)
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 12, GLvoidp(0))
    
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

        dt = time.time() - old_time
        while dt >= 1 / tickrate:
            # do logic for frame
            glRotate(6 / tickrate, 1, 0, 1.25)
            # end frame
            dt -= 1 / tickrate
            old_time = time.time()
            
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        # BEGIN DRAW
        glUseProgram(shader_program)
        glDrawElements(GL_POINTS, 8, GL_UNSIGNED_INT, GLvoidp(0))
        
##        glUseProgram(0)
##        glColor(1, 0, 1)
##        glBegin(GL_POINTS)
##        glVertex(0, 0, 0)
##        glVertex(1, 0, 0)
##        glVertex(0, 1, 0)
##        glVertex(0, 0, 1)
##        glEnd()
        
        # END DRAW
        SDL_GL_SwapWindow(window)
        

if __name__ == '__main__':
    import getopt
    import sys
    options = getopt.getopt(sys.argv[1:], 'w:h:')
    width = 512
    height = 512
    for option in options:
        for key, value in option:
            if key == '-w':
                width = int(value)
            elif key == '-h':
                height = int(value)
    main(width, height)
