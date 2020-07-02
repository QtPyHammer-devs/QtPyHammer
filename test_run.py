import sys

from PyQt5 import QtCore, QtGui, QtWidgets

from QtPyHammer.ui.core import MainWindow


def except_hook(cls, exception, traceback): # for debugging Qt slots
    sys.__excepthook__(cls, exception, traceback)
    
sys.excepthook = except_hook
app = QtWidgets.QApplication([])
# TEST CODE
window = MainWindow()
window.showMaximized()
window.new_tab(f"test_maps/{sys.argv[1]}.vmf")
# END TEST CODE
sys.exit(app.exec_())
