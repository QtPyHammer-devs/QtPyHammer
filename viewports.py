# try qopengl to keep dependecies simple & multi-platform
from OpenGL.GL import *
from OpenGL.GLU import *
from PyQt5 import QtCore, QtGui, QtWidgets

import sys
sys.path.insert(0, 'utilities') # there has to be a better way to load these
import camera
import physics
import vmf_tool
import vector
import solid_tool # must be loaded AFTER vmf_tool (how do dependencies work?)

view_modes = ['flat', 'textured', 'wireframe']
# "silhouette" view mode, lights on black brushwork & props

class Viewport2D(QtWidgets.QOpenGLWidget):
    def __init__(self, fps=30, parent=None):
        super(Viewport2D, self).__init__(parent)
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(1000 / fps)
        self.dt = 1 / fps # will desynchronise
        self.fps = fps
        # set render resolution?
        self.camera = camera.freecam(None, None, 128)
        ### BUFFERS ###
        # HELPER MODELS: (static draw)
        # shared app-wide
        # modelname: index(start, len)
        # BRUSHES: (dynamic draw)
        # brush index: vertex(start, len), index(start, len)
        # vertex buffer len
        # index buffer len
        # MODELS: (dynamic draw)
        # modelname: vertex(start, len), index(start, len)
        self.draw_calls = dict() # shader: (VERTEX_buffer, INDEX_buffer, start, end)

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
    
    def changeViewMode(self, view_mode): # overlay viewmode button
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

    def keyPressEvent(self, event): # how do>
        self.keys += event.key()
        if event.key() == QtCore.Qt.Key_Z:
            self.camera_moving = False if self.camera_moving else True
            if self.camera_moving == True:
                print('camera moving')
            else:
                print('camera stopped')

    def initializeGL(self):
        glClearColor(0, 0, 0, 0)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
##        gluPerspective(self.fov, self.width() / self.height(), 0.1, 4096 * 4)
        gluPerspective(self.fov, 1, 0.1, 4096 * 4)
        glRotate(-90, 1, 0, 0)
        glTranslate(0, 384, -64)
        glEnable(GL_DEPTH_TEST)
##        glEnable(GL_CULL_FACE)
        glPolygonMode(GL_BACK, GL_LINE)
        glFrontFace(GL_CW)
        glPointSize(4)

    def paintGL(self):
        # gluPerspective
        # rotate camera
        # draw skybox
        # translate camera
        glUseProgram(0)
        glRotate(30 * self.dt, 0, 0, 1)
        glPushMatrix()
        glLineWidth(1)
        glBegin(GL_LINES)
##        glColor(1, 0, 0)
##        glVertex(0, 0, 0)
##        glVertex(128, 0, 0)
##        glColor(0, 1, 0)
##        glVertex(0, 0, 0)
##        glVertex(0, 128, 0)
##        glColor(0, 0, 1)
##        glVertex(0, 0, 0)
##        glVertex(0, 0, 128)
        # grid
        glColor(.25, .25, .25)
        for x in range(-512, 1, 64): # segment to avoid clip warping shape
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
        glPopMatrix()

        # do draw_calls
        for shader, index_map in self.draw_calls.items():
            start, length = index_map
            glUseProgram(shader)
            glDrawElements(GL_TRIANGLES, length, GL_UNSIGNED_INT, GLvoidp(start))

    def resizeGL(self, width, height):
##        self.makeCurrent()
##        gluPerspective(self.fov, width / height, 0.1, 4096 * 4)
##        self.doneCurrent()
        pass

    def update(self):
        super(Viewport3D, self).update()
        if self.camera_moving:
            # need to sample mouse vector (relative updates)
            self.camera.update(self.mouse, self.keys, self.dt)

# WHY AREN'T CONTEXTS SHARING?  ??????????????????????
class QuadViewport(QtWidgets.QWidget): # busted
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


if __name__ == "__main__":
    import sys

    def except_hook(cls, exception, traceback):
        sys.__excepthook__(cls, exception, traceback)
    sys.excepthook = except_hook
    # ^^^ for python debugging inside Qt ^^^ #

    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts)
    app = QtWidgets.QApplication(sys.argv)
    
##    window = QuadViewport()
##    window.setGeometry(256, 256, 512, 512)
##    window.show()
    
    window = QtWidgets.QWidget()
    window.setGeometry(256, 256, 512, 512)
    layout = QtWidgets.QGridLayout()
    window.setLayout(layout)
    for y in range(2):
        for x in range(2):
            if x == 0 and y == 0:
                window.layout().addWidget(Viewport3D(30), x, y)
            else:
                window.layout().addWidget(Viewport2D(15), x, y)
    window.show()
    window.layout().itemAt(1).widget().sharedGLsetup()
    
    sys.exit(app.exec_())
