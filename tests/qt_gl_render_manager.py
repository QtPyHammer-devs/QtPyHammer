import ctypes
import itertools
import math
import struct
import time

import numpy as np
from OpenGL.GL import *
from OpenGL.GL.shaders import compileShader, compileProgram
from OpenGL.GLU import *
from PyQt5 import QtCore, QtWidgets


class render_manager:
    def __init__(self):
        self.update_queue = [] # (vertices, indices)
    
    def init_GL(self):
        glClearColor(0.25, 0.25, 0.5, 0.0)
        glEnable(GL_DEPTH_TEST)
        glEnableClientState(GL_VERTEX_ARRAY)
        gluPerspective(90, 1, 0.1, 1024)
        glTranslate(0, 0, -4)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 12, GLvoidp(0))
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
            outColour = vec4(position.xyz * 0.75, 1) + Ka; }"""
        vert_shader = compileShader(vertex_shader_source, GL_VERTEX_SHADER)
        frag_shader = compileShader(fragment_shader_source, GL_FRAGMENT_SHADER)
        self.basic_shader = compileProgram(vert_shader, frag_shader)
        glLinkProgram(self.basic_shader)
        glUseProgram(self.basic_shader)
        self.matrix_location = glGetUniformLocation(self.basic_shader, "MVP")
    
    def init_buffers(self, size=256):
        self.VERTEX_BUFFER = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.VERTEX_BUFFER)
        glBufferData(GL_ARRAY_BUFFER, size, None, GL_DYNAMIC_DRAW)
        self.INDEX_BUFFER = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.INDEX_BUFFER)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, size, None, GL_DYNAMIC_DRAW)

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

    def draw(self):
        glUseProgram(self.basic_shader)
        glDrawElements(GL_TRIANGLES, 8, GL_UNSIGNED_INT, GLvoidp(0))

    def update(self):
        if len(self.update_queue) > 0:
            vertices, indices = self.update_queue.pop(0)
            self.update_buffers(vertices, indices)
        matrix = glGetFloatv(GL_MODELVIEW_MATRIX)
        glUseProgram(self.basic_shader)
        glUniformMatrix4fv(self.matrix_location, 1, GL_FALSE, matrix)


class viewport(QtWidgets.QOpenGLWidget):
    def __init__(self):
        super(viewport, self).__init__(parent=None)
        self.render_manager = render_manager()
        self.clock = QtCore.QTimer()
        self.clock.timeout.connect(self.update)

    def initializeGL(self):
        self.render_manager.init_GL()
        self.render_manager.init_buffers()
        self.clock.start(15) # tick_length in milliseconds

    def update(self, tick_length=0.015):
        glRotate(30 * tick_length, 1, 0, 1.25)
        self.render_manager.update()
        super(viewport, self).update()

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.render_manager.draw()
        glPointSize(4)
        glUseProgram(0)
        glBegin(GL_TRIANGLES)
        glVertex(1, 0)
        glVertex(0, 1)
        glVertex(0, 0)
        glEnd()


if __name__ == '__main__':
    import sys

    def except_hook(cls, exception, traceback):
        sys.__excepthook__(cls, exception, traceback)
    sys.excepthook = except_hook # Python Qt Debug
    
    app = QtWidgets.QApplication(sys.argv)
    window = viewport()
    window.setGeometry(128, 0, 576, 576)
    vertices = [(-1, 1, 1), (1, 1, 1), (1, -1, 1), (-1, -1, 1), (-1, 1, -1), (1, 1, -1), (1, -1, -1), (-1, -1, -1)]
    indices = [0, 1, 2, 0, 2, 3, 4, 5, 6, 4, 6, 7]
    window.render_manager.update_queue.append([vertices, indices])
    window.show()
    sys.exit(app.exec_())
