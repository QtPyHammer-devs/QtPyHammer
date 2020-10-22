import math

import OpenGL.GL as gl
from OpenGL.GLU import gluPerspective
from PyQt5 import QtCore, QtGui, QtWidgets

from ..utilities import camera
from ..utilities import render
from ..utilities import vector


camera.keybinds = {camera.FORWARD: [QtCore.Qt.Key_W],
                   camera.BACK: [QtCore.Qt.Key_S],
                   camera.LEFT: [QtCore.Qt.Key_A],
                   camera.RIGHT: [QtCore.Qt.Key_D],
                   camera.UP: [QtCore.Qt.Key_Q],
                   camera.DOWN: [QtCore.Qt.Key_E]}

view_modes = ["flat", "textured", "wireframe"]
# "silhouette" view mode, lights on flat gray brushwork & props


class MapViewport3D(QtWidgets.QOpenGLWidget):  # initialised in ui/tabs.py
    raycast = QtCore.pyqtSignal(vector.vec3, vector.vec3)  # emits ray

    def __init__(self, parent=None, fps=60):
        super(MapViewport3D, self).__init__(parent=parent)
        preferences = QtWidgets.QApplication.instance().preferences
        camera.sensitivity = float(preferences.value("Input/MouseSensitivity", "2.0"))
        # ^ this shouldn't be here, but it has to be set once the app is active
        # RENDERING
        self.render_manager = render.manager()
        # model draw distance (defined in settings)
        self.ray = (vector.vec3(), vector.vec3())  # origin, dir (for debug rendering)
        # INPUT HANDLING
        self.camera = camera.freecam(None, None, 16)
        self.camera_moving = False
        self.cursor_start = QtCore.QPoint()
        self.moved_last_tick = False
        self.keys = set()  # currently held keyboard keys
        self.current_mouse_position = vector.vec2()
        self.last_mouse_position = vector.vec2()
        self.mouse_vector = vector.vec2()
        self.setFocusPolicy(QtCore.Qt.ClickFocus)
        # ^ to get mouse inputs, user must click on the viewport
        # REFRESH TIMER
        self.dt = 1 / fps
        self.timer = QtCore.QTimer()
        self.timer.setInterval(1000 / fps)
        self.timer.timeout.connect(self.update)
        # be aware, the timer does not have an accumulator
        # desynchronisations will occur

    def update(self):  # called on timer once initializeGL is run
        self.makeCurrent()
        self.render_manager.update()
        self.doneCurrent()
        super(MapViewport3D, self).update()  # calls PaintGL

    ######################
    ### OpenGL Methods ###
    ######################

    def initializeGL(self):
        self.render_manager.init_GL()
        self.set_view_mode("flat")  # sets shaders & GL state
        self.timer.start()

    # calling the slot by it's name creates a QVariant Error
    # which for some reason does not trace correctly
    @QtCore.pyqtSlot(str, name="setViewMode")  # connected to UI
    def set_view_mode(self, view_mode):  # C++: void setViewMode(QString)
        self.view_mode = view_mode
        self.makeCurrent()
        if view_mode == "flat":
            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)
            gl.glDisable(gl.GL_TEXTURE_2D)
        elif view_mode == "textured":
            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)
            gl.glEnable(gl.GL_TEXTURE_2D)
            # add textures to buffers
        elif view_mode == "wireframe":
            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_LINE)
            gl.glDisable(gl.GL_TEXTURE_2D)
        self.doneCurrent()

    def paintGL(self):
        mouse = QtGui.QCursor.pos()
        self.current_mouse_position = vector.vec2(mouse.x(), mouse.y())
        self.mouse_vector = self.current_mouse_position - self.last_mouse_position
        if self.camera_moving:
            self.setMouseTracking(False)
            center = self.mapToGlobal(QtCore.QPoint(self.width() / 2, self.height() / 2))
            QtGui.QCursor.setPos(center)
            self.setMouseTracking(True)
            self.last_mouse_position = vector.vec2(center.x(), center.y())
        self.moved_last_tick = True
        # ^ get accurate mouse input for frame
        gl.glLoadIdentity()
        fov = self.render_manager.fov
        aspect = self.render_manager.aspect
        draw_distance = self.render_manager.draw_distance
        gl.gluPerspective(fov, aspect, 0.1, draw_distance)
        # UPDATE CAMERA
        ms = self.timer.remainingTime() / self.timer.interval() / 1000
        if self.camera_moving:  # TOGGLED ON: take user inputs
            self.camera.update(self.mouse_vector, self.keys, self.dt + ms)
            if self.moved_last_tick is False:  # prevent drift
                self.mouse_vector = vector.vec2()
            self.moved_last_tick = False
        self.camera.set()
        # ^ cannot call gluPerspective in render.manager.draw
        # -- this order of operations must be preserved
        # if rendering a skybox, it must be rendering after camera rotation & before camera position
        # -- may also want to stencil render skybox brushes
        self.render_manager.draw()
        super(MapViewport3D, self).paintGL()

    def resizeGL(self, width, height):
        self.render_manager.aspect = width / height

    ##################
    ### Qt Signals ###
    ##################

    def do_raycast(self, click_x, click_y):
        camera_right = vector.vec3(x=1).rotate(*-self.camera.rotation)
        camera_up = vector.vec3(z=1).rotate(*-self.camera.rotation)
        camera_forward = vector.vec3(y=1).rotate(*-self.camera.rotation)
        width, height = self.width(), self.height()
        x_offset = camera_right * ((click_x * 2 - width) / width)
        x_offset *= width / height  # aspect ratio
        y_offset = camera_up * ((click_y * 2 - height) / height)
        fov_scalar = math.tan(math.radians(self.render_manager.fov / 2))
        x_offset *= fov_scalar
        y_offset *= fov_scalar
        ray_origin = self.camera.position
        ray_direction = camera_forward + x_offset + y_offset
        self.ray = (ray_origin, ray_direction)  # <-- for debug render
        return ray_origin, ray_direction

    ##########################
    ### Rebound Qt Methods ###
    ##########################

    def keyPressEvent(self, event):  # not registering arrow keys?
        self.keys.add(event.key())

        def free_mouse():
            self.setMouseTracking(False)
            QtGui.QCursor.setPos(self.cursor_start)
            self.unsetCursor()
            self.releaseMouse()
        if event.key() == QtCore.Qt.Key_Z:
            self.camera_moving = False if self.camera_moving else True
            if self.camera_moving:
                self.setMouseTracking(True)
                self.cursor_start = QtGui.QCursor.pos()
                self.last_mouse_position = vector.vec2(self.cursor_start.x(), self.cursor_start.y())
                self.grabMouse()
                self.setCursor(QtCore.Qt.BlankCursor)
            else:
                free_mouse()
        elif event.key() == QtCore.Qt.Key_Escape and self.camera_moving:
            free_mouse()

    def keyReleaseEvent(self, event):
        self.keys.discard(event.key())

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:  # defined in settings
            x, y = event.pos().x(), event.pos().y()
            if self.camera_moving:
                x = self.width() / 2
                y = self.height() / 2
            ray_origin, ray_direction = self.do_raycast(x, self.height() - y)
            self.raycast.emit(ray_origin, ray_direction)
        super(MapViewport3D, self).mouseReleaseEvent(event)

    def wheelEvent(self, event):
        if self.camera_moving:
            self.camera.speed = max(self.camera.speed + event.angleDelta().y(), 1)

    def leaveEvent(self, event):  # cursor leaves widget
        if self.camera_moving:
            center = QtCore.QPoint(self.width() / 2, self.height() / 2)
            QtGui.QCursor.setPos(self.mapToGlobal(center))
        super(MapViewport3D, self).leaveEvent(event)

    def hideEvent(self, event):
        super(MapViewport3D, self).hideEvent(event)
        self.timer.stop()

    def showEvent(self, event):
        super(MapViewport3D, self).showEvent(event)
        self.timer.start()


class MapViewport2D(QtWidgets.QOpenGLWidget):  # QtWidgets.QGraphicsView ?
    def __init__(self, fps=30, parent=None):
        self.fps = fps
        self.timer = QtCore.QTimer()
        self.timer.setInterval(1000 / fps)
        self.timer.timeout.connect(self.update)
        self.dt = 1 / fps  # time elapsed for update() (camera.velocity *= dt)
        # ^ will desynchronise, use time.time()
        self.camera = camera.freecam(None, None, 128)
        super(MapViewport2D, self).__init__(parent)
        self.setFocusPolicy(QtCore.Qt.ClickFocus)  # get mouse input
