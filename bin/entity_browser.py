import fgdtools
from PyQt5 import QtCore, QtGui, QtWidgets
import sys

def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)
sys.excepthook = except_hook

app = QtWidgets.QApplication(sys.argv)
window = QtWidgets.QMainWindow()
window.setwindowTitle('Entity Browser')
window.setGeometry(640, 400, 640, 480)

# key | value fields for entities
# drop down list to choose entity
# hints per entry

# look at hammer screenies

window.show()

app.exec_()
