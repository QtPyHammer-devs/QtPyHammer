import math
import sys

import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *
from PyQt5 import QtCore, QtGui, QtWidgets

sys.path.insert(0, "../")
from utilities import camera
from utilities import render
from utilities import vector


# arrow keys aren't registering? why? do we need a separate function?
camera.keybinds = {'FORWARD': [QtCore.Qt.Key_W], 'BACK': [QtCore.Qt.Key_S],
                   'LEFT': [QtCore.Qt.Key_A, QtCore.Qt.LeftArrow],
                   'RIGHT': [QtCore.Qt.Key_D, QtCore.Qt.RightArrow],
                   'UP': [QtCore.Qt.Key_Q, QtCore.Qt.UpArrow],
                   'DOWN': [QtCore.Qt.Key_E, QtCore.Qt.DownArrow]}
# ^ defined in settings ^
camera.sensitivity = 2 # defined in settings

view_modes = ['flat', 'textured', 'wireframe']
# "silhouette" view mode, lights on flat gray brushwork & props


class MapViewport3D(QtWidgets.QOpenGLWidget): # initialised in ui/tabs.py
    raycast = QtCore.pyqtSignal(vector.vec3, vector.vec3) # emits ray
    # ^ https://www.riverbankcomputing.com/static/Docs/PyQt5/signals_slots.html
    def __init__(self, parent, fps=60):
        super(MapViewport3D, self).__init__(parent=parent)
        # RENDERING
        self.render_manager = parent.render_manager
        self.draw_distance = 4096 * 4 # defined in settings
        self.fov = 90 # defined in settings (70 - 120)
        self.GLES_MODE = False # store GL version instead?
        # model draw distance (defined in settings)
        self.view_mode = "flat" # defined in settings
        self.ray = [] # origin, dir (for debug rendering)
        # INPUT HANDLING
        self.camera = camera.freecam(None, None, 128)
        self.camera_moving = False
        self.cursor_start = QtCore.QPoint()
        self.moved_last_tick = False
        self.keys = set() # currently held keyboard keys
        self.current_mouse_position = vector.vec2()
        self.mouse_vector = vector.vec2()
        self.setFocusPolicy(QtCore.Qt.ClickFocus) # get mouse inputs
        # REFRESH RATE
        self.fps = fps
        self.dt = 1 / fps # will desynchronise, use time.time()
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)

    def start(self):
        self.timer.start(1000 / self.fps) # start painting

    def show(self): # must show widget to create context
        super(MapViewport3D, self).show() # make a context that can be shared
        print("viewport GL context")
        print("isValid", self.context().isValid())
        self.context().setShareContext(self.render_manager.gl_context)
        self.context().reset()
        self.context().create()
        print("SHARING", self.context().areSharing(self.render_manager.gl_context))
        # check sharing has occured
        # INVALID QVARIANT
        # BAD sharing
        # SET FORMAT?
        # then use GL objects created by render_manager pre-sharing
        self.set_view_mode("flat")
        # ^ view mode must be set so we can grab the correct shaders
        # self.start()

    @QtCore.pyqtSlot(str, name="setViewMode") # connected to UI
    def set_view_mode(self, view_mode): # C++: void setViewMode(QString)
        print("calling set_view_mode")
        raise RuntimeError()
        self.view_mode = view_mode
        self.shaders = self.render_manager.shader[view_mode]
        self.uniforms = self.render_manager.uniform[view_mode]
        self.makeCurrent()
        if view_mode == "flat":
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
            glDisable(GL_TEXTURE_2D)
        elif view_mode == "textured":
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
            glEnable(GL_TEXTURE_2D)
            # add textures to buffers
        elif view_mode == "wireframe":
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
            glDisable(GL_TEXTURE_2D)
        self.doneCurrent()
        print("called set_view_mode")

    def do_raycast(self):
        if self.camera_moving: # cast the ray from the middle of the camera
            ray_origin = self.camera.position
            ray_direction = vector.vec3(y=1).rotate(*-self.camera.rotation)
        else: # cast the ray from the cursor
            # en.wikipedia.org/wiki/Ray_tracing_(graphics)#Calculate_rays_for_rectangular_viewport
            click = vector.vec2(((event.pos().x() / self.width()) * 2) - 1,
                                ((event.pos().y() / self.width()) * 2) - 1)
                                # ^ scale by width because aspect ratio ^
            ray_origin += vector.vec3(click.x, 0, -click.y).rotate(*-self.camera.rotation)
            self.makeCurrent()
            matrix = glGetFloatv(GL_PROJECTION_MATRIX)
            self.doneCurrent()
            perspective_dir = np.matmul(matrix, [click.x, -click.y, 1, 1])
            # ^ aligns with camera but angle is incorrect
            ray_direction = vector.vec3(*perspective_dir[:3]).normalise()
        self.ray = [ray_origin, ray_direction] # for debug rendering
        return ray_origin, ray_direction

    # REBINDING QT METHODS
    def keyPressEvent(self, event):
        self.keys.add(event.key())
        if event.key() == QtCore.Qt.Key_Z:
            self.camera_moving = False if self.camera_moving else True
            if self.camera_moving: # start tracking cursor
                self.setMouseTracking(True)
                self.cursor_start = QtGui.QCursor.pos()
                center = QtCore.QPoint(self.width() / 2, self.height() / 2)
                QtGui.QCursor.setPos(self.mapToGlobal(center))
                self.grabMouse()
                self.setCursor(QtCore.Qt.BlankCursor)
            else: # free camera
                self.setMouseTracking(False)
                QtGui.QCursor.setPos(self.cursor_start)
                self.unsetCursor()
                self.releaseMouse()
        if self.camera_moving and event.key() == QtCore.Qt.Key_Escape:
            self.setMouseTracking(False)
            self.unsetCursor()
            self.releaseMouse()

    def keyReleaseEvent(self, event):
        self.keys.discard(event.key())

    def wheelEvent(self, event):
        if self.camera_moving:
            self.camera.speed += event.angleDelta().y()

    # Mouse Action = mousePressEvent -> mouseMoveEvent -> mouseReleaseEvent
    def mousePressEvent(self, event): # start of click
        button = event.button()
        position = event.pos()
        # tell mouseMoveEvent to record position until mouseReleaseEvent
        # mouseReleaseEvent will then call a function if hotkeys were pressed
        # but only if they were pressed here in mousePressEvent
        # (at the start of the mouse action)
        ...
        # self.do_raycast
        # emit the ray to ui/tabs.py:Workspace
        # or save the result of the raycast and return with the mouse action
        ...
        # if button == middle mouse:
        #     do: blender camera
        super(MapViewport3D, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        # use blender camera controls when not self.camera_moving
        if self.camera_moving:
            center = QtCore.QPoint(self.width() / 2, self.height() / 2)
            self.current_mouse_position = vector.vec2(event.pos().x(), event.pos().y())
            self.mouse_vector = self.current_mouse_position - vector.vec2(center.x(), center.y())
            QtGui.QCursor.setPos(self.mapToGlobal(center))
            self.moved_last_tick = True
        super(MapViewport3D, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event): # end of click
        if event.button() == QtCore.Qt.LeftButton: # defined in settings
            ray_origin, ray_direction = self.do_raycast()
            self.raycast.emit(ray_origin, ray_direction)
        super(MapViewport3D, self).mouseReleaseEvent(event)

    def initializeGL(self):
        self.setViewMode(self.view_mode) # IT WAS MEEEEEE
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
        render.draw_grid()
        render.draw_origin()
        # loop over targets (brush, displacement, model)
        glUseProgram(self.shaders["brush"]) # did not share context?
## Like buffer and texture objects, the name space for program objects may
## be shared across a set of contexts, as long as the server sides of the
## contexts share the same address space. If the name space is shared
## across contexts, any attached objects and the data associated with those
## attached objects are shared as well. Applications are responsible for
## providing the synchronization across API calls when objects are accessed
## from different execution threads.
## ERRORS:
## GL_INVALID_VALUE : program is neither 0 nor a value generated by OpenGL.
## GL_INVALID_OPERATION : program is not a program object.
## GL_INVALID_OPERATION : program could not be made part of current state.
## GL_INVALID_OPERATION : transform feedback mode is active.
        for uniform, location in self.uniforms["brush"].items():
            # {"uniform": [func, *args]} would be better
            # since it allows us to share uniforms across shaders
            if uniform == "matrix":
                glUniformMatrix4fv(matrix_loc, 1, GL_FALSE, matrix)
        # dither for flat shaded transparency on skip & hint
        for span in self.render_manager.abstract_buffer_map["index"]["brushes"]:
            # ^ overly long name for a commonly used array ^
            start, length = span
            glDrawElements(GL_TRIANGLES, length, GL_UNSIGNED_INT, GLvoidp(start))
        if self.ray != []: # render raycast for debug
            glUseProgram(0)
            glColor(1, .75, .25)
            glLineWidth(2)
            glBegin(GL_LINES)
            glVertex(*self.ray[0])
            glVertex(*(self.ray[0] + self.ray[1] * self.draw_distance))
            glEnd()
            glLineWidth(1)

    def resizeGL(self, width, height):
        glLoadIdentity()
        gluPerspective(self.fov, self.width() / self.height(), 0.1, 4096 * 4)

    def update(self):
        if self.camera_moving: # TOGGLED ON: take user inputs
            self.camera.update(self.mouse_vector, self.keys, self.dt)
            if self.moved_last_tick == False: # prevent drift
                self.mouse_vector = vector.vec2()
            self.moved_last_tick = False
        super(MapViewport3D, self).update() # calls PaintGL


class MapViewport2D(QtWidgets.QOpenGLWidget): # QtWidgets.QGraphicsView ?
    def __init__(self, fps=30, parent=None):
        self.fps = fps
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(1000 / fps)
        self.dt = 1 / fps # time elapsed for update() (camera.velocity *= dt)
        # ^ will desynchronise, use time.time()
        self.camera = camera.freecam(None, None, 128)
        super(MapViewport2D, self).__init__(parent)
        self.setFocusPolicy(QtCore.Qt.ClickFocus) # get mouse input
