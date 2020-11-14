import itertools
import struct

import numpy as np
from OpenGL.GL import *
from OpenGL.GL.shaders import compileShader, compileProgram
from OpenGL.GLU import gluPerspective
from PyQt5 import QtCore, QtWidgets


class render_manager:
    def __init__(self):
        self.update_queue = []  # (vertices, indices)

    def init_GL(self):
        glClearColor(0.25, 0.25, 0.5, 0.0)
        glEnable(GL_DEPTH_TEST)
        glEnableClientState(GL_VERTEX_ARRAY)
        gluPerspective(90, 1, 0.1, 1024)
        glTranslate(0, 0, -8)
        glPointSize(4)
        vertex_shader_source = """#version 300 es
        layout(location = 0) in vec3 vertex_position;
        uniform mat4 MVP;
        out vec3 position;
        void main() {
            position = vertex_position;
            gl_Position = MVP * vec4(vertex_position, 1); }"""
        fragment_shader_source = """#version 300 es
        layout(location = 0) out mediump vec4 outColour;
        in mediump vec3 position;
        void main() {
            mediump vec4 Ka = vec4(0.15, 0.15, 0.15, 1);
            outColour = vec4(0.75, 0.75, 0.75, 1) + Ka; }"""
        vert_shader = compileShader(vertex_shader_source, GL_VERTEX_SHADER)
        frag_shader = compileShader(fragment_shader_source, GL_FRAGMENT_SHADER)
        self.basic_shader = compileProgram(vert_shader, frag_shader)
        glLinkProgram(self.basic_shader)
        glUseProgram(self.basic_shader)
        self.matrix_location = glGetUniformLocation(self.basic_shader, "MVP")
        self.draw_length = 0

    def init_buffers(self, size=256):
        self.VERTEX_BUFFER = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.VERTEX_BUFFER)
        glBufferData(GL_ARRAY_BUFFER, size, None, GL_DYNAMIC_DRAW)
        self.INDEX_BUFFER = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.INDEX_BUFFER)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, size, None, GL_DYNAMIC_DRAW)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 12, GLvoidp(0))

    def draw(self):
        glUseProgram(self.basic_shader)
        glDrawElements(GL_TRIANGLES, self.draw_length, GL_UNSIGNED_INT, GLvoidp(0))

    def update(self):
        if len(self.update_queue) > 0:
            vertices, indices = self.update_queue.pop(0)
            self.update_buffers(vertices, indices)
        MV_matrix = glGetFloatv(GL_MODELVIEW_MATRIX)
        glUseProgram(self.basic_shader)
        glUniformMatrix4fv(self.matrix_location, 1, GL_FALSE, MV_matrix)

    def update_buffers(self, vertices, indices):
        # SEND DATA TO BUFFERS
        vertex_data = list(itertools.chain(*vertices))
        vertex_data = np.array(vertex_data, dtype=np.float32)
        glBufferSubData(GL_ARRAY_BUFFER, 0, len(vertex_data) * 4, vertex_data)
        index_data = np.array(indices, dtype=np.uint32)
        glBufferSubData(GL_ELEMENT_ARRAY_BUFFER, 0, len(index_data) * 4, index_data)
        # CHECK DATA RECIEVED
        vertex_data = glGetBufferSubData(GL_ARRAY_BUFFER, 0, len(vertices) * 3 * 4)
        vertex_data = list(struct.iter_unpack("3f", vertex_data))
        index_data = glGetBufferSubData(GL_ELEMENT_ARRAY_BUFFER, 0, len(indices) * 4)
        index_data = list(itertools.chain(*struct.iter_unpack("I", index_data)))
        assert vertex_data == vertices
        assert index_data == indices
        self.draw_length = len(indices)


class viewport(QtWidgets.QOpenGLWidget):
    def __init__(self):
        super(viewport, self).__init__(parent=None)
        self.render_manager = render_manager()
        self.clock = QtCore.QTimer()
        self.clock.timeout.connect(self.update)

    def initializeGL(self):
        self.render_manager.init_GL()
        self.render_manager.init_buffers()
        self.clock.start(15)  # tick_length in milliseconds

    def update(self, tick_length=0.015):
        self.makeCurrent()
        glRotate(30 * tick_length, 1, 0, 1.25)
        self.render_manager.update()
        self.doneCurrent()
        super(viewport, self).update()  # calls paintGL

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.render_manager.draw()
        glUseProgram(0)
        glBegin(GL_TRIANGLES)
        glVertex(1, 0)
        glVertex(0, 1)
        glVertex(0, 0)
        glEnd()


if __name__ == '__main__':
    vertices = [(-1, 1, 1), (1, 1, 1), (1, -1, 1), (-1, -1, 1),
                (-1, 1, -1), (1, 1, -1), (1, -1, -1), (-1, -1, -1)]
    indices = [0, 1, 2, 0, 2, 3, 4, 5, 6, 4, 6, 7]

    TEST = "QT"

    if TEST == "QT":
        import sys

        def except_hook(cls, exception, traceback):
            sys.__excepthook__(cls, exception, traceback)
        sys.excepthook = except_hook  # Python Qt Debug

        app = QtWidgets.QApplication(sys.argv)
        window = viewport()
        window.setGeometry(128, 64, 576, 576)
        window.render_manager.update_queue.append([vertices, indices])
        window.show()
        app.exec_()

    elif TEST == "SDL":
        import ctypes
        from sdl2 import *
        import time

        def sdl_window(width=576, height=576):
            SDL_Init(SDL_INIT_VIDEO)
            window = SDL_CreateWindow(b"SDL2 OpenGL",
                                      SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
                                      width, height,
                                      SDL_WINDOW_OPENGL | SDL_WINDOW_BORDERLESS)
            glContext = SDL_GL_CreateContext(window)
            SDL_GL_SetSwapInterval(0)
            manager = render_manager()
            manager.init_GL()
            manager.init_buffers()
            global vertices, indices
            manager.update_queue.append([vertices, indices])
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
                    glRotate(30 / tickrate, 1, 0, 1.25)
                    manager.update()
                    # end frame
                    dt -= 1 / tickrate
                    old_time = time.time()
                glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
                manager.draw()
                glUseProgram(0)
                glBegin(GL_TRIANGLES)
                glVertex(0, 1)
                glVertex(1, 0)
                glVertex(0, 0)
                glEnd()
                SDL_GL_SwapWindow(window)

        sdl_window()
