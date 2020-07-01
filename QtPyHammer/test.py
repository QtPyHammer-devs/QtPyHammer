import os
import sys

from PyQt5 import QtCore, QtGui, QtWidgets

import ui.core


def except_hook(cls, exception, traceback): # for debugging Qt slots
    sys.__excepthook__(cls, exception, traceback)
    
sys.excepthook = except_hook
app = QtWidgets.QApplication(sys.argv)
# TEST CODE
window = ui.core.MainWindow()
window.showMaximized()
current_dir = dir_path = os.path.dirname(os.path.realpath(__file__)) + "/"
window.new_tab(current_dir + "../test_maps/pl_upward_d.vmf")
# END TEST CODE
sys.exit(app.exec_())
