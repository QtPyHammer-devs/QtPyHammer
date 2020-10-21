import pytest
import pytestqt

from QtPyHammer.ui.core import MainWindow


def test_MainWindow(qtbot):
    window = MainWindow()
    window.show()
    qtbot.addWidget(window)
    assert window.windowTitle() == "QtPyHammer"
