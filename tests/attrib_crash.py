#!/usr/bin/env python
import ctypes

# third party imports
import numpy as np
from OpenGL.GL import *
from OpenGL.GL.shaders import compileShader, compileProgram
from sdl2 import * # Try with an SDL2 glContext


def main(width=512, height=512):
        window = glCreateWindow(b'test', SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED, width, height, SDL_WINDOW_OPENGL | SDL_WINDOW_BORDERLESS)
        context = SDL_GL_CreateContext(window)

        shaders = "../src/main/resources/base/shaders/GLSL_300/"
        cs = lambda s, t: compileShader(open(shaders + s, "rb"), t)
        # vertex shaders
        vs_brush = cs("brush.vert", GL_VERTEX_SHADER)
        vs_displacement = cs("displacement.vert", GL_VERTEX_SHADER)
        # fragment shaders
        fs_brush = cs("flat_brush.frag", GL_FRAGMENT_SHADER)
        fs_displacement = cs("flat_displacement.frag", GL_FRAGMENT_SHADER)

        p_brush = compileProgram(vs_brush, fs_brush)
        p_displacement = compileProgram(vs_displacement, fs_displacement)
        glLinkProgram(p_brush)
        glLinkProgram(p_displacement)

        glUseProgram(p_brush)
        u_matrix_brush = glGetUniformLocation(p_brush, "ModelViewProjectionMatrix")
        glUseProgram(p_displacement)
        u_matrix_displacement = glGetUniformLocation(p_displacement, "ModelViewProjectionMatrix")
        glUseProgram(0)

        vertices = []
        indices = []
        # 44 bytes BRUSH SPEC
        # ?? bytes DISP SPEC

        # vertex Buffer
        VERTEX_BUFFER, INDEX_BUFFER = glGenBuffers(2)
        glBindBuffer(GL_ARRAY_BUFFER, VERTEX_BUFFER)
        glBufferData(GL_ARRAY_BUFFER, len(vertices) * 4,
                     np.array(vertices, dtype=np.float32), GL_STATIC_DRAW)
        # index Buffer
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, INDEX_BUFFER)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, len(indices) * 4,
                     np.array(indices, dtype=np.uint32), GL_STATIC_DRAW)

        # vertex Format
        glEnableVertexAttribArray(0) # vertex_position
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 44, GLvoidp(0))
        glEnableVertexAttribArray(1) # vertex_normal (brush only)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_TRUE, 44, GLvoidp(12))
        # glEnableVertexAttribArray(4) # blend_alpha (displacement only)
        glVertexAttribPointer(4, 1, GL_FLOAT, GL_FALSE, 44, GLvoidp(12))
        # ^ replaces vertex_normal if displacement ^
        glEnableVertexAttribArray(2) # vertex_uv
        glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 44, GLvoidp(24))
        glEnableVertexAttribArray(3) # editor_colour
        glVertexAttribPointer(3, 3, GL_FLOAT, GL_FALSE, 44, GLvoidp(32))

        ...
