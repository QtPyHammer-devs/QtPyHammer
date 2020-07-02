import sys

from PyQt5 import QtCore, QtGui, QtWidgets

from QtPyHammer.ui.core import MainWindow


def except_hook(cls, exception, traceback): # for debugging Qt slots
    sys.__excepthook__(cls, exception, traceback)
    
sys.excepthook = except_hook
app = QtWidgets.QApplication(sys.argv)
# load user config(s)
# read .fgd(s) for entity_data
# prepare .vpks (grab directories)
# mount & tag custom data (check the gameinfo.txt for paths, accept others)
window = MainWindow()
window.showMaximized()
sys.exit(app.exec_())
