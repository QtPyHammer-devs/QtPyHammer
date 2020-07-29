import os
import sys

from PyQt5 import QtCore, QtGui, QtWidgets

from QtPyHammer.ui.core import MainWindow
from QtPyHammer.ui.user_preferences.theme import load_theme


def except_hook(cls, exception, traceback): # for debugging Qt slots
    sys.__excepthook__(cls, exception, traceback)
sys.excepthook = except_hook

app = QtWidgets.QApplication([])
app.setStyle(QtWidgets.QStyleFactory.create("Fusion"))

preferences = QtCore.QSettings("configs/preferences.ini", QtCore.QSettings.IniFormat)
default_game = preferences.value("Default/Game", "Team Fortress 2")
app.game_config = QtCore.QSettings("configs/games/{default_game}.ini", QtCore.QSettings.IniFormat)
default_theme = preferences.value("Default/Theme", "light_mode")

themes = dict()
for filename in os.listdir("configs/themes/"):
    theme_name = filename.rpartition(".")[0] # filename without extention
    themes[theme_name] = load_theme(f"configs/themes/{filename}")
app.setPalette(themes[default_theme])
if sys.platform == "win32":
    reg = QtCore.QSettings("HKEY_CURRENT_USER/Software/Microsoft/Windows/CurrentVersion/Themes/Personalize", QtCore.QSettings.NativeFormat)
    if reg.value("AppsUseLightTheme") == 0:
        app.setPalette(themes[dark_mode])
        app.setStyleSheet("QToolTip { color: #ffffff; background-color: #2a82da; border: 1px solid white; }")

print(QtWidgets.QApplication.instance() == app)

window = MainWindow()
window.showMaximized()
window.new_tab(f"Team Fortress 2/tf/mapsrc/{sys.argv[1]}.vmf")
sys.exit(app.exec_())
