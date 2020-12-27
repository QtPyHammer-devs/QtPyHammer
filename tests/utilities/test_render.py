from PyQt5 import QtWidgets

from QtPyHammer.utilities import render


class TestRenderManager:
    def test_render_manager(qtbot):
        gl_widget = QtWidgets.QOpenGLWidget()
        render_manager = render.Manager(2048, 90, 256)
        qtbot.addWidget(gl_widget)
