import sys

from PyQt5 import QtWidgets

sys.path.insert("../../src/main/python/ui")
import entity


def except_hook(cls, exception, traceback): #for PyQt debugging
    sys.__excepthook__(cls, exception, traceback)
sys.excepthook = except_hook


app = QtWidgets.QApplication(sys.argv)
window = entity.browser()
window.setWindowTitle('Entity Browser')
window.setGeometry(640, 400, 640, 480)
window.show()
app.exec_()
