import sys

from PyQt5 import QtCore, QtGui, QtWidgets

from QtPyHammer.ui.core import MainWindow
from QtPyHammer.ops.palette import load_palette


def except_hook(cls, exception, traceback): # for debugging Qt slots
    sys.__excepthook__(cls, exception, traceback)
sys.excepthook = except_hook

app = QtWidgets.QApplication([])
app.setStyle(QtWidgets.QStyleFactory.create("Fusion"))
# load all palettes os.listdir
light_mode = load_palette("light_mode")
dark_mode = load_palette("dark_mode")
# set the default from settings.ini # test_run.py will use private_setting.ini (add to .gitignore)
app.setPalette(light_mode) # default palette
if sys.platform == "win32":
    reg = QtCore.QSettings("HKEY_CURRENT_USER/Software/Microsoft/Windows/CurrentVersion/Themes/Personalize", QtCore.QSettings.NativeFormat)
    if reg.value("AppsUseLightTheme") == 0:
        app.setPalette(dark_mode)
        app.setStyleSheet("QToolTip { color: #ffffff; background-color: #2a82da; border: 1px solid white; }")

window = MainWindow()
window.showMaximized()
window.new_tab(f"Team Fortress 2/tf/mapsrc/{sys.argv[1]}.vmf")
sys.exit(app.exec_())
