from PyQt5 import QtWidgets

from . import theme

# combine all user preferences tabs into one, loading from config.ini
# connect it all to ops


class settings_editor(QtWidgets.QTabWidget):
    def __init__(self, parent):
        QtWidgets.QDialog.__init__(self, parent)  # become a Dialog
        self.addTab(theme.theme_editor(self), "Theme")


if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    window = settings_editor(None)
    window.setGeometry(128, 128, 512, 576)
    window.show()

    app.exec_()
