import sys

from PyQt5 import QtCore, QtGui, QtWidgets

from QtPyHammer.ui.core import MainWindow


def except_hook(cls, exception, traceback): # for debugging Qt slots
    sys.__excepthook__(cls, exception, traceback)
    
sys.excepthook = except_hook
app = QtWidgets.QApplication(sys.argv)
# TEST CODE
window = MainWindow()
window.showMaximized()
window.new_tab("test_maps/pl_upward_d.vmf")
# END TEST CODE
sys.exit(app.exec_())
