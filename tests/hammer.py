from QtPyHammer.ui.core import MainWindow


def test_MainWindow(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    assert window.windowTitle() == "QtPyHammer"
