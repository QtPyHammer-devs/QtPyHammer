from __future__ import annotations
import os  # TODO: use pathlib instead
import sys
from typing import Any, Dict, List

import valvefgd
from PyQt5 import QtCore, QtWidgets

from QtPyHammer.ui.core import MainWindow
from QtPyHammer.ui.user_preferences.theme import load_theme


# TODO: session restore / shutdown warning (unsaved data will be lost etc.)


def load_ini(ini: str) -> QtCore.QSettings:
    # NOTE: a python wrapper for QSettings would be nice
    # -- type conversion (from string)
    # NOTE: default settings should be stored someplace in python
    # -- so we can restore defaults & highlight changes
    return QtCore.QSettings(ini, QtCore.QSettings.IniFormat)


class QtPyHammerApp(QtWidgets.QApplication):
    # NOTE: this data can be accessed anywhere in QtPyHammer by calling:
    # -- QtWidgets.QApplication.instance()
    fgd: valvefgd.Fgd
    folder: str
    game_config: QtCore.QSettings
    hotkeys: QtCore.QSettings
    preferences: QtCore.QSettings
    themes: Dict[str, Any]
    # ^ {theme_name: theme}

    def __init__(self, argv: List[str]):
        super(QtWidgets.QApplication, self).__init__(argv)

        # gather global data
        self.folder = os.path.dirname(__file__)

        self.preferences = load_ini("configs/preferences.ini")

        game = self.preferences.value("Game", "Team Fortress 2")
        self.game_config = load_ini(f"configs/games/{game}.ini")

        self.hotkeys = load_ini("configs/controls/hammer.ini")

        # TODO: check gameinfo.txt for extra content paths
        # -- allow the user to load custom content from their own folders
        # -- then copy that content to tf/custom/{vmf.filename} on compile

        # get & set themes
        self.themes = dict()
        for filename in os.listdir("configs/themes/"):
            # strip extension before attempting to load theme
            theme_name = filename.rpartition(".")[0]
            self.themes[theme_name] = load_theme(f"configs/themes/{filename}")
        theme = self.preferences.value("Theme", "default")
        if theme not in self.themes:
            theme = "default"

        self.setStyle(QtWidgets.QStyleFactory.create("Fusion"))
        self.setPalette(self.themes[theme])
        # Windows Theme
        if sys.platform == "win32":
            reg = QtCore.QSettings(
                "\\".join([
                    "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows",
                    "CurrentVersion\\Themes\\Personalize"]),
                QtCore.QSettings.NativeFormat)
            # Dark Mode
            if reg.value("AppsUseLightTheme") == 0:
                dark_theme = f"{theme}_dark"
                if dark_theme not in self.themes:
                    dark_theme = "default_dark"
                self.setPalette(self.themes[dark_theme])
                self.setStyleSheet("""
                    QToolTip {
                      color: #ffffff;
                      background-color: #2a82da;
                      border: 1px solid white;
                    }""")
                # ^ TODO: allow themes to include .css files
                # -- and have them locked to individual widgets?

        # startup .fgd cache
        fgd_file = self.game_config.value("Hammer/GameData0")
        self.fgd = valvefgd.parser.FgdParse(fgd_file)


if __name__ == "__main__":
    # NOTE: not passing any arguments to the QApplication
    app = QtPyHammerApp([])

    window = MainWindow()
    window.showMaximized()

    # attempt to load filenames from arguments
    for filename in sys.argv[1:]:
        window.open(filename)

    sys.exit(app.exec())
