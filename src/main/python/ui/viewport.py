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
# ^ connect to settings ^

view_modes = ['flat', 'textured', 'wireframe']
# "silhouette" view mode, lights on flat gray brushwork & props

class Viewport2D(QtWidgets.QOpenGLWidget): # why not QtWidgets.QGraphicsView ?
    def __init__(self, fps=30, parent=None):
        super(Viewport2D, self).__init__(parent)
        self.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(1000 / fps)
        self.dt = 1 / fps # will desynchronise, use time.time()
        self.fps = fps
        # lower resolution and scale up option
        self.camera = camera.freecam(None, None, 128)
        self.draw_calls = dict() # function: {**kwargs}

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
        # create a texture so we know we're sharing
        glEnable(GL_TEXTURE_2D)
        black = b'\xFF\xAF\x00\x00'
        purple = b'\x00\xFF\xAF\x00'
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 2, 2, 0,
                     GL_RGBA, GL_UNSIGNED_BYTE, black + purple + purple + black)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glColor(1, 1, 1)
        # end shared content creation
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

    def update(self): # once every tick
        super(Viewport2D, self).update() # calls paintGL


class Viewport3D(Viewport2D):
    def __init__(self, fps=30, view_mode='flat', parent=None):
        super(Viewport3D, self).__init__(fps=fps, parent=parent)
        # RENDERING
        self.buffer_updates = []
        self.draw_calls = dict() # function: {**kwargs}
        # function shouldn't be the keys
        # {"groupname": [function, [args], {kwargs}], ...}
        # would allow modifying the args with a simple string key
        self.draw_distance = 4096 * 4 # Z-plane cull (load from a config)
        self.fov = 90 # how do users change this?
        self.GLES_MODE = False # store full GL version instead?
        # model draw distance (load from a config)
        self.view_mode = view_mode
        # INPUTS
        self.camera_moving = False
        self.cursor_start = QtCore.QPoint()
        self.moved_last_tick = False
        self.keys = set()
        self.current_mouse_position = vector.vec2()
        self.mouse_vector = vector.vec2()

        # RAYCAST DEBUG / VISUALISER
        self.ray = [] # origin, dir
        def draw_ray(viewport):
            glUseProgram(0)
            if viewport.ray == []:
                return
            glColor(1, .75, .25)
            glLineWidth(2)
            glBegin(GL_LINES)
            glVertex(*viewport.ray[0])
            glVertex(*(viewport.ray[1] * viewport.draw_distance) + viewport.ray[0])
            glEnd()
            glLineWidth(1)
        self.draw_calls[draw_ray] = {}

    def changeViewMode(self, view_mode): # overlay viewmode button
        if self.view_mode == view_mode:
            return # exit, no changes needed
        if self.view_mode == "flat":
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
            glDisable(GL_TEXTURE_2D)
            # flat shaders
        elif view_mode == "textured":
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
            glEnable(GL_TEXTURE_2D)
            # textured shaders
            # how do textures get looked up?
        elif view_mode == "wireframe":
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
            glDisable(GL_TEXTURE_2D)
            # flat shaders

    def keyPressEvent(self, event):
        self.keys.add(event.key())
        if event.key() == QtCore.Qt.Key_Z:
            self.camera_moving = False if self.camera_moving else True
            # https://stackoverflow.com/questions/9774929/qt-keeping-mouse-centered
            if self.camera_moving:
                self.setMouseTracking(True)
                self.cursor_start = QtGui.QCursor.pos()
                center = QtCore.QPoint(self.width() / 2, self.height() / 2)
                QtGui.QCursor.setPos(self.mapToGlobal(center))
                self.grabMouse()
                self.setCursor(QtCore.Qt.BlankCursor)
            else:
                self.setMouseTracking(False)
                QtGui.QCursor.setPos(self.cursor_start)
                self.unsetCursor()
                self.releaseMouse()
        if event.key() == QtCore.Qt.Key_Escape and self.camera_moving:
            self.setMouseTracking(False)
            self.unsetCursor()
            self.releaseMouse()

    def keyReleaseEvent(self, event):
        self.keys.discard(event.key())

    def mouseMoveEvent(self, event):
        if self.camera_moving: # only reset when the cursor is hidden to
            center = QtCore.QPoint(self.width() / 2, self.height() / 2)
            self.current_mouse_position = vector.vec2(event.pos().x(), event.pos().y())
            self.mouse_vector = self.current_mouse_position - vector.vec2(center.x(), center.y())
            QtGui.QCursor.setPos(self.mapToGlobal(center)) # center cursor
            self.moved_last_tick = True
        super(Viewport3D, self).mouseMoveEvent(event)

    def mousePressEvent(self, event):
        button = event.button()
        position = event.pos()
        super(Viewport3D, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton: # register as a QAction? rebindable
            # send a signal / slot
            # cast from center
            ray_origin = self.camera.position
            ray_direction = vector.vec3(y=1).rotate(*-self.camera.rotation)
            if not self.camera_moving: # ray may be off-center
                click = vector.vec2(((event.pos().x() / self.width()) * 2) - 1,
                                    ((event.pos().y() / self.height()) * 2) - 1)
                # doesn't appear to compensate for aspect ratio
                ray_origin += vector.vec3(click.x, 0, -click.y).rotate(*-self.camera.rotation)
                self.makeCurrent()
                matrix = glGetFloatv(GL_PROJECTION_MATRIX)
                self.doneCurrent()
                perspective_dir = np.matmul(matrix, [click.x, -click.y, 1, 1])
                # ^ aligns with camera but doesn't shift out far enough
                ray_direction = vector.vec3(*perspective_dir[:3]).normalise()
            self.ray = [ray_origin, ray_direction]
        super(Viewport3D, self).mouseReleaseEvent(event)

    def wheelEvent(self, event):
        if self.camera_moving:
            self.camera.speed += event.angleDelta().y()

    def initializeGL(self):
        glClearColor(0, 0, 0, 0)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.fov, self.width() / self.height(), 0.1, self.draw_distance)
        glEnable(GL_DEPTH_TEST)
##        glEnable(GL_CULL_FACE)
        glPolygonMode(GL_BACK, GL_LINE)
        glFrontFace(GL_CW)
        glPointSize(4)

    def paintGL(self):
        glLoadIdentity()
        gluPerspective(self.fov, self.width() / self.height(), 0.1, self.draw_distance)
        self.camera.set()
        if self.GLES_MODE:
            matrix = glGetFloatv(GL_PROJECTION_MATRIX)
        # try to minimise state changes between draw calls
        # i.e. UseProgram(0) once and only once
        # group by state changes
        # want to draw as many objects as possible with the fewest states
        # also reusing functions with alternate states
        # e.g. dither for flat shading transparency on certain visgroups
        for func, kwargs in self.draw_calls.items():
            func(self, **kwargs)

    def resizeGL(self, width, height):
        glLoadIdentity()
        gluPerspective(self.fov, self.width() / self.height(), 0.1, 4096 * 4)

    def update(self):
        super(Viewport3D, self).update()
        if self.camera_moving: # TOGGLED ON: take user inputs
            self.camera.update(self.mouse_vector, self.keys, self.dt)
            if self.moved_last_tick == False: # prevent drift
                self.mouse_vector = vector.vec2()
            self.moved_last_tick = False
        for func in self.buffer_updates[::]:
            func(self)
            self.buffer_updates.remove(func)

### === ????? WHY AREN'T CONTEXTS SHARING ?????? === ###
# can we just share GL objects between contexts?
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
