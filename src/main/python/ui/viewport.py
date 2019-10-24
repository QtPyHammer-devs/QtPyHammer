import math
import sys

import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *
from PyQt5 import QtCore, QtGui, QtWidgets

sys.path.insert(0, "../")
from utilities import camera, vector


# arrow keys aren't registering? why? do we need a separate function?
# these should also be overridden when loading settings
camera.keybinds = {'FORWARD': [QtCore.Qt.Key_W], 'BACK': [QtCore.Qt.Key_S],
                   'LEFT': [QtCore.Qt.Key_A, QtCore.Qt.LeftArrow],
                   'RIGHT': [QtCore.Qt.Key_D, QtCore.Qt.RightArrow],
                   'UP': [QtCore.Qt.Key_Q, QtCore.Qt.UpArrow],
                   'DOWN': [QtCore.Qt.Key_E, QtCore.Qt.DownArrow]}
camera.sensitivity = 2

view_modes = ['flat', 'textured', 'wireframe']
# "silhouette" view mode, lights on flat gray brushwork & props

class Viewport2D(QtWidgets.QOpenGLWidget):
    def __init__(self, fps=30, parent=None):
        super(Viewport2D, self).__init__(parent)
        self.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(1000 / fps)
        self.dt = 1 / fps # will desynchronise, use time.time()
        self.fps = fps
        # set render resolution?
        self.camera = camera.freecam(None, None, 128)
        self.draw_calls = dict() # shader: (index buffer start, end)

    def executeGL(self, func, *args, **kwargs): # best hack ever
        """Execute func(self, *args, **kwargs) in this viewport's glContext"""
        self.makeCurrent()
        func(self, *args, **kwargs)
        self.doneCurrent()

    def resizeGL(self, width, height):
        x_scale = width / height
        glLoadIdentity()
        glOrtho(-x_scale, x_scale, -1, 1, 0, 1024)

    def initializeGL(self):
        glClearColor(0, 0, 0, 0)
        # glEnables
        glColor(.75, .75, .75)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        glEnable(GL_TEXTURE_2D)

    def sharedGLsetup(self): # call once when sharing context with others
        """Sets up buffers, textures & shaders shared across many viewports"""
        self.makeCurrent()
        glEnable(GL_TEXTURE_2D)
        black = b'\xFF\xAF\x00\x00'
        purple = b'\x00\xFF\xAF\x00'
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 2, 2, 0,
                     GL_RGBA, GL_UNSIGNED_BYTE, black + purple + purple + black)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glColor(1, 1, 1)
        self.doneCurrent()
##        return buffer_handles, shader_handles, texture_handles

    def paintGL(self): # how do we use Qt OpenGL functions?
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glEnable(GL_TEXTURE_2D)
        glRotate(self.dt * 90, 0, 0, 1)
        glBegin(GL_TRIANGLES)
        glTexCoord(1, 0)
        glVertex(1, 0, 0)
        glTexCoord(-1, 0)
        glVertex(-1, 0, 0)
        glTexCoord(0, 1)
        glVertex(0, 1, 0)
        glEnd()

        # do draw_calls

    def update(self):
        super(Viewport2D, self).update()
        # update animations (TICKS)
        # just to keep logic seperate
        # super().update() calls paintGL


class Viewport3D(Viewport2D):
    def __init__(self, fps=30, view_mode='flat', parent=None):
        super(Viewport3D, self).__init__(fps=fps, parent=parent)
        self.view_mode = view_mode
        self.fov = 90 # how do users change this?
        self.camera_moving = False
        self.camera_keys = list()
        self.draw_calls = dict() # shader: (start, length)
        self.GLES_MODE = False
        self.keys = set()
        self.current_mouse_position = vector.vec2()
        self.previous_mouse_position = vector.vec2()
        self.mouse_vector = vector.vec2()
        self._perspective = (90, 0.1, 10234)

    def changeViewMode(self, view_mode): # overlay viewmode button
        # if GLES_MODE = True
        # shaders MUST be used
        if self.view_mode == view_mode:
            return # exit, no changes needed
        if self.view_mode == 'wireframe':
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        if view_mode == 'textured':
            glEnable(GL_TEXTURE_2D)
        else:
            glDisable(GL_TEXTURE_2D)
        if view_mode == 'wireframe':
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
            return # polygon mode, shaders off, textures off
        # change shader to flat (flat / wireframe)
        # or to complex (textured)

    def keyPressEvent(self, event):
        self.keys.add(event.key())
        if event.key() == QtCore.Qt.Key_Z:
            self.camera_moving = False if self.camera_moving else True
            # remember where the cursor was when tracking
            # move to center while hidden (move back after every update)
            # move mouse back to starting position once finished
            if self.camera_moving:
                self.setMouseTracking(True)
                self.grabMouse()
                self.setCursor(QtCore.Qt.BlankCursor)
                # keep teleporting the mouse back to the center
                # teleport to entry point when free
            else:
                self.setMouseTracking(False)
                self.unsetCursor()
                self.releaseMouse()
        if event.key() == QtCore.Qt.Key_Escape and self.camera_moving:
            self.setMouseTracking(False)
            self.unsetCursor()
            self.releaseMouse()

    def keyReleaseEvent(self, event):
        self.keys.discard(event.key())

    def mouseMoveEvent(self, event):
        self.previous_mouse_position = self.current_mouse_position # use center (we teleport back there after each camera.update())
        self.current_mouse_position = vector.vec2(event.pos().x(), event.pos().y())
        self.mouse_vector = self.current_mouse_position - self.previous_mouse_position

    def wheelEvent(self, event):
        if self.camera_moving:
            self.camera.speed += event.angleDelta().y()

    def initializeGL(self):
        glClearColor(0, 0, 0, 0)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.fov, self.width() / self.height(), 0.1, 4096 * 4)
        glEnable(GL_DEPTH_TEST)
##        glEnable(GL_CULL_FACE)
        glPolygonMode(GL_BACK, GL_LINE)
        glFrontFace(GL_CW)
        glPointSize(4)

    def printMatrix(self):
        print(glGetFloatv(GL_MODELVIEW_MATRIX))

    def paintGL(self):
        glPushMatrix()
        self.camera.set()
        if self.GLES_MODE:
            far, near = 0.1, 4096 # same as in gluPerspective ^^^
            s = 1 / math.tan(self.fov / 2)
            MVP_matrix = np.array([s, 0, 0, 0,
                                   0, s, 0, 0,
                                   0, 0, -far / (far - near), -1,
                                   self.camera.position.x, self.camera.position.y, (-far * near / (far - near)) + self.camera.position.z, 0], np.float32)
            ### ^^^ re-calculate P (Perspective) in resizeGL ^^^ ###
            position = self.camera.position
            T = [1, 0, 0, 0,
                 0, 1, 0, 0,
                 0, 0, 1, 0,
                 -position.x, -position.y, -position.z, 1]
            theta = self.camera.rotation.x
            Rx = [1, 0, 0, 0,
                  0, math.cos(theta), -math.sin(theta), 0,
                  0, math.sin(theta), math.cos(theta), 0,
                  0, 0, 0, 1]
            theta = self.camera.rotation.y
            Ry = [math.cos(theta), 0, math.sin(theta), 0,
                  0, 1, 0, 0,
                  -math.sin(theta), 0, math.cos(theta), 0,
                  0, 0, 0, 1]
            theta = self.camera.rotation.z
            Rz = [math.cos(theta), -math.sin(theta), 0, 0,
                  math.sin(theta), math.cos(theta), 0, 0,
                  0, 0, 1, 0,
                  0, 0, 0, 1]

            # MVP_matrix = T * Rx * Ry * Rz * P
            # CALCULATE ALL THIS AFTER CAMERA UPDATES!
            # keep it as a private class variable
            # but only if GLES_MODE == True


        glUseProgram(0)
##        # orbit center at 30 degrees per second
##        self.camera.rotation.z = (self.camera.rotation.z + 30 * self.dt) % 360
##        self.camera.position = self.camera.position.rotate(0, 0, -30 * self.dt)
        glBegin(GL_LINES) # GRID
        glColor(.25, .25, .25)
        for x in range(-512, 1, 64): # break up to avoid clipping plane warp
            for y in range(-512, 1, 64):
                glVertex(x, y)
                glVertex(x, -y)
                glVertex(-x, y)
                glVertex(-x, -y)
                glVertex(y, x)
                glVertex(-y, x)
                glVertex(y, -x)
                glVertex(-y, -x)
        glEnd()

        for shader, index_map in self.draw_calls.items(): # DRAW CALLS
            start, length = index_map
            glUseProgram(shader)
            if self.GLES_MODE == True:
                glUniformMatrix4fv(self.uniforms[shader], 1, GL_FALSE, MVP_matrix)
            glDrawElements(GL_TRIANGLES, length, GL_UNSIGNED_INT, GLvoidp(start))

        glPopMatrix()

    def resizeGL(self, width, height):
        glLoadIdentity()
        gluPerspective(self.fov, self.width() / self.height(), 0.1, 4096 * 4)

    def update(self):
        super(Viewport3D, self).update()
        if self.camera_moving:
            self.camera.update(self.mouse_vector, self.keys, self.dt)
            self.mouse_vector = vector.vec2()
            # teleport mouse to screen center instead ([0, 0] or something else?)

### === ????? WHY AREN'T CONTEXTS SHARING ?????? === ###
class QuadViewport(QtWidgets.QWidget): # busted, borked, no work good
    def __init__(self, parent=None):
        super(QuadViewport, self).__init__(parent)
        quad_layout = QtWidgets.QGridLayout()
        for y in range(2):
            for x in range(2):
                if x == 0 and y == 0:
                    quad_layout.addWidget(Viewport3D(30), x, y)
                else:
                    quad_layout.addWidget(Viewport2D(15), x, y)
        self.setLayout(quad_layout)

    def show(self, *args, **kwargs):
        super(QuadViewport, self).show(*args, **kwargs)
        self.layout().itemAt(1).widget().sharedGLsetup()
