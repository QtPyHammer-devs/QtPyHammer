from PyQt5 import QtWidgets

from . import theme

# combine all user preferences tabs into one, loading from config.ini
# connect it all to ops


class SettingsEditor(QtWidgets.QTabWidget):
    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)
        # ^ initialise as a QDialog, this means we have a floating dialog that tabs can be directly added to
        # -- maybe there's a better way to do multiple inheritance...
        self.addTab(theme.ThemeEditor(self), "Theme")
