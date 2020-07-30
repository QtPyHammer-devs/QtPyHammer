import os
import sys

import fgdtools
from PyQt5 import QtCore, QtGui, QtWidgets

from QtPyHammer.ui.core import MainWindow
from QtPyHammer.ui.user_preferences.theme import load_theme


def except_hook(cls, exception, traceback): # for debugging Qt slots
    sys.__excepthook__(cls, exception, traceback)
sys.excepthook = except_hook

app = QtWidgets.QApplication([])
# ^ app can be accessed from anywhere with QtWidgets.QApplication.instance()

# load all config files
app.preferences = QtCore.QSettings("configs/preferences.ini", QtCore.QSettings.IniFormat)
game = app.preferences.value("Game", "Team Fortress 2")
app.game_config = QtCore.QSettings(f"configs/games/{game}.ini", QtCore.QSettings.IniFormat)
app.hotkeys = QtCore.QSettings("configs/hotkeys.ini", QtCore.QSettings.IniFormat)

app.themes = dict()
for filename in os.listdir("configs/themes/"):
    theme_name = filename.rpartition(".")[0] # filename without extention
    app.themes[theme_name] = load_theme(f"configs/themes/{filename}")
theme = app.preferences.value("Theme", "default")
if theme not in app.themes:
    theme = "default"
app.setStyle(QtWidgets.QStyleFactory.create("Fusion"))
app.setPalette(app.themes[theme])

if sys.platform == "win32":
    reg = QtCore.QSettings("HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize", QtCore.QSettings.NativeFormat)
    if reg.value("AppsUseLightTheme") == 0:
        dark_theme = f"{theme}_dark"
        if dark_theme not in app.themes:
            dark_theme = "default_dark"
        app.setPalette(app.themes[dark_theme])
        app.setStyleSheet("QToolTip { color: #ffffff; background-color: #2a82da; border: 1px solid white; }")
        # ^ allow themes to include .css files
        # -- will need some way to indicate which widgets have them set

# load all entities from the .fgd
##fgd_file = app.game_config.value("Hammer/GameData0") # the .fgd
fgd_file = "Team Fortress 2/bin/tf.fgd"
app.fgd = fgdtools.parser.FgdParse(fgd_file)

# check gameinfo.txt for extra content paths
# allow the user to load custom content from their own folders
# then copy that content to tf/custom/{vmf.filename} on compile

window = MainWindow()
window.showMaximized()
window.new_tab(f"Team Fortress 2/tf/mapsrc/{sys.argv[1]}.vmf") # <-- TEST
sys.exit(app.exec_())
