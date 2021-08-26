from PyQt5 import QtWidgets

from QtPyHammer.utilities import render


class TestRenderManager:
    def test_init(self, qtbot):  # WIP
        gl_widget = QtWidgets.QOpenGLWidget()
        render_manager = render.Manager(2048, 90, 256)
        gl_widget.initializeGL = render_manager.initGL()
        qtbot.addWidget(gl_widget)
