import pytest
import pytestqt

from QtPyHammer.ui.core import MainWindow


# QtPyHammer app is initialised in conftest.py, just testing the main window opens.
def test_hammer_main_window(qtbot):
    window = MainWindow()
    window.show()
    qtbot.addWidget(window)
    assert window.windowTitle() == "QtPyHammer"

# def test_no_fgd(qtbot):  # need to remove the fgd from the app to test ui.core's reaction to it's abscence
    # with pytest.raises(RuntimeError):
        # window = MainWindow()
        # window.show()
        # qtbot.addWidget(window)
        
# def test_new_file(qtbot):
        
# def test_open_file(qtbot):

# test clicking some things with the whole app open, get lots of deep coverage
