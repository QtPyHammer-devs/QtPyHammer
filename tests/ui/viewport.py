import os
import sys

from PyQt5 import QtCore, QtWidgets

sys.path.insert(0, "../src/main/python")
from ui import viewport


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)
sys.excepthook = except_hook

viewport.camera.sensitivity = 4
# LOAD AND TESTS UI ELEMENTS
QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts)
app = QtWidgets.QApplication(sys.argv)

##window = viewport.QuadViewport()
##window.setGeometry(256, 256, 512, 512)
##window.show()

##window = QtWidgets.QWidget()
##window.setGeometry(256, 256, 512, 512)
##layout = QtWidgets.QGridLayout()
##window.setLayout(layout)
##for y in range(2):
##    for x in range(2):
##        if x == 0 and y == 0:
##            window.layout().addWidget(viewport.Viewport3D(30), x, y)
##        else:
##            window.layout().addWidget(viewport.Viewport2D(15), x, y)
##window.show()
##window.layout().itemAt(1).widget().sharedGLsetup()

window = viewport.Viewport3D(60)
window.camera.position += (0, -384, 64)
window.setGeometry(256, 256, 512, 512)
window.show()

sys.exit(app.exec_())
