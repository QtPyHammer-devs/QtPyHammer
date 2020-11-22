import ctypes
import itertools
import struct
import time

import numpy as np
import OpenGL.GL as gl
from OpenGL.GL.shaders import compileShader, compileProgram
import sdl2


def main(width, height):
    sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO)
    window = sdl2.SDL_CreateWindow(b"SDL2 OpenGL",
                                   sdl2.SDL_WINDOWPOS_CENTERED,
                                   sdl2.SDL_WINDOWPOS_CENTERED,
                                   width, height,
                                   sdl2.SDL_WINDOW_OPENGL | sdl2.SDL_WINDOW_BORDERLESS)
    glContext = sdl2.SDL_GL_CreateContext(window)
    sdl2.SDL_GL_SetSwapInterval(0)
    gl.glClearColor(0.25, 0.25, 0.5, 0.0)
    gl.glEnable(gl.GL_DEPTH_TEST)
    gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
    gl.gluPerspective(90, 1, 0.1, 1024)
    gl.glTranslate(0, 0, -8)
    gl.glPointSize(4)

    # BEGIN SHADERS
    # VERT SHADER SOURCE
    vertex_shader_core_source = """#version 450 core
    layout(location = 0) in vec3 vertex_position;
    uniform mat4 gl_ModelViewProjectionMatrix;
    out vec3 position;

    void main()
    {
        position = vertex_position;
        gl_Position = gl_ModelViewProjectionMatrix * vec4(vertex_position, 1);
    }"""
    vertex_shader_gles_source = """#version 300 es
    layout(location = 0) in vec3 vertex_position;
    uniform mat4 ModelViewProjectionMatrix;
    out vec3 position;

    void main()
    {
        position = vertex_position;
        gl_Position = ModelViewProjectionMatrix * vec4(vertex_position, 1);
    }"""
    # FRAG SHADER SOURCE
    fragment_shader_core_source = """#version 450 core
    layout(location = 0) out vec4 outColour;
    in vec3 position;

    void main()
    {
        vec4 Ka = vec4(0.15, 0.15, 0.15, 1);
        outColour = vec4(position.xyz * 0.75, 1) + Ka;
    }"""
    fragment_shader_gles_source = """#version 300 es
    layout(location = 0) out mediump vec4 outColour;
    in mediump vec3 position;

    void main()
    {
        mediump vec4 Ka = vec4(0.15, 0.15, 0.15, 1);
        outColour = vec4(position.xyz * 0.75, 1) + Ka;
    }"""

    major = gl.glGetIntegerv(gl.GL_MAJOR_VERSION)
    minor = gl.glGetIntegerv(gl.GL_MINOR_VERSION)

    if major >= 4 and minor >= 5:
        GLES = False
        vert_source = vertex_shader_core_source
        frag_source = fragment_shader_core_source
    else:
        GLES = True
        vert_source = vertex_shader_gles_source
        frag_source = fragment_shader_gles_source

    vert_shader = compileShader(vert_source, gl.GL_VERTEX_SHADER)
    frag_shader = compileShader(frag_source, gl.GL_FRAGMENT_SHADER)

    shader_program = compileProgram(vert_shader, frag_shader)
    gl.glLinkProgram(shader_program)
    gl.glUseProgram(shader_program)
    if GLES:
        matrix_location = gl.glGetUniformLocation(shader_program, "ModelViewProjectionMatrix")
    # END SHADERS

    # BEGIN DYNAMIC DRAW BUFFER TEST
    # VERTEX
    cube_vertices = [(-1, 1, 1), (1, 1, 1), (1, -1, 1), (-1, -1, 1),
                     (-1, 1, -1), (1, 1, -1), (1, -1, -1), (-1, -1, -1)]
    cube_vertices = [*itertools.chain(*cube_vertices)]
    cube_vertices = np.array(cube_vertices, dtype=np.float32)

    VERTEX_BUFFER = gl.glGenBuffers(1)
    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, VERTEX_BUFFER)
    gl.glBufferData(gl.GL_ARRAY_BUFFER, 256, None, gl.GL_DYNAMIC_DRAW)
    gl.glBufferSubData(gl.GL_ARRAY_BUFFER, 0, len(cube_vertices) * 4, cube_vertices)
    # ^ target, start, length, *data

    # CHECK
    vertex_buffer_data = gl.glGetBufferSubData(gl.GL_ARRAY_BUFFER, 0, 8 * 3 * 4)
    # ^ target, start, length
    vertices = list(struct.iter_unpack("3f", vertex_buffer_data))
    print(vertices)

    # INDEX
    cube_indices = [0, 1, 2,  0, 2, 3,
                    4, 5, 6,  4, 6, 7]
    cube_indices = np.array(cube_indices, dtype=np.uint32)

    INDEX_BUFFER = gl.glGenBuffers(1)
    gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, INDEX_BUFFER)
    gl.glBufferData(gl.GL_ELEMENT_ARRAY_BUFFER, 256, None, gl.GL_DYNAMIC_DRAW)
    gl.glBufferSubData(gl.GL_ELEMENT_ARRAY_BUFFER, 0, len(cube_indices) * 4, cube_indices)
    # ^ target, start, length, *data

    # CHECK
    index_buffer_data = gl.glGetBufferSubData(gl.GL_ELEMENT_ARRAY_BUFFER, 0, 8 * 4)
    # ^ target, start, length
    indices = [s[0] for s in struct.iter_unpack("I", index_buffer_data)]
    print(indices)
    #  END DYNAMIC DRAW BUFFER TEST  #

    gl.glEnableVertexAttribArray(0)
    gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, 12, gl.GLvoidp(0))

    tickrate = 1 / 0.015
    tick_number = 0
    old_time = time.time()
    event = sdl2.SDL_Event()
    while True:
        while sdl2.SDL_PollEvent(ctypes.byref(event)) != 0:
            if event.type == sdl2.SDL_QUIT or event.key.keysym.sym == sdl2.SDLK_ESCAPE and event.type == sdl2.SDL_KEYDOWN:
                sdl2.SDL_GL_DeleteContext(glContext)
                sdl2.SDL_DestroyWindow(window)
                sdl2.SDL_Quit()
                return False

        dt = time.time() - old_time
        while dt >= 1 / tickrate:
            # do logic for frame
            gl.glRotate(30 / tickrate, 1, 0, 1.25)
            if GLES:
                MV_matrix = gl.glGetFloatv(gl.GL_MODELVIEW_MATRIX)
                # P_matrix = gl.glGetFloatv(gl.GL_PROJECTION_MATRIX)
                gl.glUseProgram(shader_program)
                gl.glUniformMatrix4fv(matrix_location, 1, gl.GL_FALSE, MV_matrix)
            if tick_number % 20 == 0:
                cube_indices = [(i + 1) % 8 for i in cube_indices]
                gl.glBufferSubData(gl.GL_ELEMENT_ARRAY_BUFFER,
                                   0, 12 * 4,
                                   np.array(cube_indices, dtype=np.uint32))
            tick_number = (tick_number + 1) % 60
            # end frame
            dt -= 1 / tickrate
            old_time = time.time()

        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        # BEGIN DRAW
        gl.glUseProgram(shader_program)
        gl.glDrawElements(gl.GL_TRIANGLES, len(cube_indices), gl.GL_UNSIGNED_INT, gl.GLvoidp(0))
        # END DRAW
        sdl2.SDL_GL_SwapWindow(window)


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
