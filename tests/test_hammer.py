# from PyQt5 import QtCore

from QtPyHammer.ui.core import MainWindow
from QtPyHammer.ui.workspace import VmfTab


# QtPyHammer app is initialised in conftest.py, just testing the main window opens.
class TestHammer:
    def load_hammer(self, qtbot):
        self.hammer = MainWindow()
        qtbot.addWidget(self.hammer)

    def test_initialises(self, qtbot):
        self.load_hammer(qtbot)
        assert self.hammer.windowTitle() == "QtPyHammer"

    # def test_no_fgd(self, qtbot):
    #     # remove the .fgd from the app & test the reaction to it's abscence
    #     with pytest.raises(RuntimeError):
    #         window = MainWindow()
    #         window.show()
    #         qtbot.addWidget(window)

    def test_new_file(self, qtbot):
        self.load_hammer(qtbot)
        self.hammer.actions["File>New"].trigger()
        qtbot.waitUntil(lambda: self.hammer.tabs.currentIndex() == 0)
        assert isinstance(self.hammer.tabs.widget(0), VmfTab)

    # def test_open_file(self, qtbot):
    #     self.load_hammer(qtbot)
    #     self.hammer.actions["File>Open"].trigger()
    #     qtbot.mouseClick(hammer.mapBrowser.?, QtCore.Qt.LeftButton)
    #     qtbot.waitUntil(lambda: self.hammer.tabs.currentIndex() == 0, 2000)
    #     assert isinstance(self.hammer.tabs.widget(0), VmfTab)

# TODO: test some example actions a user might make, recreate bugs
