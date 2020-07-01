import sys

from PyQt5 import QtCore, QtGui, QtWidgets

import ui.core


def except_hook(cls, exception, traceback): # for debugging Qt slots
    sys.__excepthook__(cls, exception, traceback)
    
sys.excepthook = except_hook
app = QtWidgets.QApplication(sys.argv)
# load user config(s)
# read .fgd(s) for entity_data
# prepare .vpks (grab directories)
# mount & tag custom data (check the gameinfo.txt for paths, accept others)
window = ui.core.MainWindow()
window.showMaximized()
sys.exit(app.exec_())