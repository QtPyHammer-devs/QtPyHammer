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
    window = SDL_CreateWindow(b"SDL2 OpenGL", SDL_WINDOWPOS_CENTERED,  SDL_WINDOWPOS_CENTERED, width, height, SDL_WINDOW_OPENGL | SDL_WINDOW_BORDERLESS)
    glContext = SDL_GL_CreateContext(window)
    SDL_GL_SetSwapInterval(0)
    glClearColor(0.0, 0.05, 0.1, 0.0)
##    glOrtho(-2, 2, -2, 2, 0, 1024)
    # ^ left, right, bottom, top, near, far
    gluPerspective(90, 1, 0.1, 1024)
    # ^ fov, aspect, near, far
    glTranslate(0, 0, -4)
    
    glEnable(GL_DEPTH_TEST)
    glEnableClientState(GL_VERTEX_ARRAY)
    
    ###  BEGIN DYNAMIC DRAW BUFFER TEST  ###
    # VERTEX
    cube_vertices = [(-1, 1, 1), (1, 1, 1), (1, -1, 1), (-1, -1, 1),
                     (-1, 1, -1), (1, 1, -1), (1, -1, -1), (-1, -1, -1)]
    cube_vertices = [*itertools.chain(*cube_vertices)]
    cube_vertices = np.array(cube_vertices, dtype=np.float32)

    VERTEX_BUFFER = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, VERTEX_BUFFER)
    glBufferData(GL_ARRAY_BUFFER, 256, None, GL_DYNAMIC_DRAW)
    glBufferSubData(GL_ARRAY_BUFFER, 0, len(cube_vertices) * 4, cube_vertices)
    # ^ target, start, length, *data

    # CHECK
    vertex_buffer_data = glGetBufferSubData(GL_ARRAY_BUFFER, 0, 8 * 3 * 4)
    # ^ target, start, length
    vertices = list(struct.iter_unpack("3f", vertex_buffer_data))
    print(vertices)

    # INDEX
    cube_indices = [0, 1, 2,  0, 2, 3,
                    4, 5, 6,  4, 6, 7]
    cube_indices = np.array(cube_indices, dtype=np.uint32)

    INDEX_BUFFER = glGenBuffers(1)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, INDEX_BUFFER)
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, 256, None, GL_DYNAMIC_DRAW)
    glBufferSubData(GL_ELEMENT_ARRAY_BUFFER, 0, len(cube_indices) * 4, cube_indices)
    # ^ target, start, length, *data
    
    # CHECK
    index_buffer_data = glGetBufferSubData(GL_ELEMENT_ARRAY_BUFFER, 0, 8 * 4)
    # ^ target, start, length
    indices = [s[0] for s in struct.iter_unpack("I", index_buffer_data)]
    print(indices)
    ###  END DYNAMIC DRAW BUFFER TEST  ###

    glEnableVertexAttribArray(0)
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 12, GLvoidp(0))

    ###  BEGIN SHADERS  ###
    # VERT SHADER SOURCE
    vertex_shader_core_source = """#version 450 core
    layout(location = 0) in vec3 vertex_position;
    uniform mat4 gl_ModelViewProjectionMatrix;
    out vec3 position;
    
    void main()
    {
        position = vertex_position;
        gl_Position = gl_ModelViewProjectionMatrix * vec4(vertex_position, 1);
    }
    """
    vertex_shader_gles_source = """#version 300 es
    layout(location = 0) in vec3 vertex_position;
    uniform mat4 ModelViewProjectionMatrix;
    out vec3 position;
    
    void main()
    {
        position = vertex_position;
        gl_Position = ModelViewProjectionMatrix * vec4(vertex_position, 1);
    }
    """
    
    # FRAG SHADER SOURCE
    fragment_shader_core_source = """#version 450 core
    layout(location = 0) out vec4 outColour;
    in vec3 position;

    void main()
    {
        vec4 Ka = vec4(0.15, 0.15, 0.15, 1);
        outColour = vec4(position.xyz * 0.75, 1) + Ka;
    }
    """
    fragment_shader_gles_source = """#version 300 es
    layout(location = 0) out mediump vec4 outColour;
    in mediump vec3 position;

    void main()
    {
        mediump vec4 Ka = vec4(0.15, 0.15, 0.15, 1);
        outColour = vec4(position.xyz * 0.75, 1) + Ka;
    }
    """

    major = glGetIntegerv(GL_MAJOR_VERSION)
    minor = glGetIntegerv(GL_MINOR_VERSION)

    if major >= 4 and minor >= 5:
        GLES = False
        vert_source = vertex_shader_core_source
        frag_source = fragment_shader_core_source
    else:
        GLES = True
        vert_source = vertex_shader_gles_source
        frag_source = fragment_shader_gles_source
    
    vert_shader = compileShader(vert_source, GL_VERTEX_SHADER)
    frag_shader = compileShader(frag_source, GL_FRAGMENT_SHADER)

    shader_program = compileProgram(vert_shader, frag_shader)
    glLinkProgram(shader_program)
    glUseProgram(shader_program)
    if GLES:
        matrix_location = glGetUniformLocation(shader_program, "ModelViewProjectionMatrix")
    ###  END SHADERS  ###
    
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

        dt = time.time() - old_time
        while dt >= 1 / tickrate:
            # do logic for frame
            glRotate(30 / tickrate, 1, 0, 1.25)
            if GLES:
                MV_matrix = glGetFloatv(GL_MODELVIEW_MATRIX)
                P_matrix = glGetFloatv(GL_PROJECTION_MATRIX)
                glUseProgram(shader_program)
                glUniformMatrix4fv(matrix_location, 1, GL_FALSE, MV_matrix)
            if tick_number % 20 == 0:
                cube_indices = [(i + 1) % 8 for i in cube_indices]
                glBufferSubData(GL_ELEMENT_ARRAY_BUFFER,
                                0, 12 * 4,
                                np.array(cube_indices, dtype=np.uint32))
            tick_number = (tick_number + 1) % 60
            # end frame
            dt -= 1 / tickrate
            old_time = time.time()
            
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        # BEGIN DRAW
        glUseProgram(shader_program)
        glDrawElements(GL_TRIANGLES, len(cube_indices), GL_UNSIGNED_INT, GLvoidp(0))
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
