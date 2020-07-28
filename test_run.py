import sys

from PyQt5 import QtCore, QtGui, QtWidgets

from QtPyHammer.ui.core import MainWindow


def except_hook(cls, exception, traceback): # for debugging Qt slots
    sys.__excepthook__(cls, exception, traceback)
sys.excepthook = except_hook

app = QtWidgets.QApplication([])
# DARK MODE
app.setStyle(QtWidgets.QStyleFactory.create("Fusion"))
palette = QtGui.QPalette
dark_palette = palette()
base = QtGui.QColor(45, 45, 45)
locked = QtGui.QColor(127, 127, 127)
dark_palette.setColor(palette.Window, base)
dark_palette.setColor(palette.WindowText, QtCore.Qt.white)
dark_palette.setColor(palette.Base, QtGui.QColor(18,18,18))
dark_palette.setColor(palette.AlternateBase, base)
dark_palette.setColor(palette.ToolTipBase, QtCore.Qt.white)
dark_palette.setColor(palette.ToolTipText, QtCore.Qt.white)
dark_palette.setColor(palette.Text, QtCore.Qt.white);
dark_palette.setColor(palette.Disabled, palette.Text, locked)
dark_palette.setColor(palette.Button, base)
dark_palette.setColor(palette.ButtonText, QtCore.Qt.white)
dark_palette.setColor(palette.Disabled, palette.ButtonText, locked)
dark_palette.setColor(palette.BrightText, QtCore.Qt.red)
dark_palette.setColor(palette.Link, QtGui.QColor(42, 130, 218))
dark_palette.setColor(palette.Highlight, QtGui.QColor(42, 130, 218))
dark_palette.setColor(palette.HighlightedText, QtCore.Qt.black)
dark_palette.setColor(palette.Disabled, palette.HighlightedText, locked)
# qpalette.light, midlight, dark, mid, shadow
app.setPalette(dark_palette)
app.setStyleSheet("QToolTip { color: #ffffff; background-color: #2a82da; border: 1px solid white; }")

# TEST CODE
window = MainWindow()
window.showMaximized()
window.new_tab(f"test_maps/{sys.argv[1]}.vmf")
# END TEST CODE
sys.exit(app.exec_())
