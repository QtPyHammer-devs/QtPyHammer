from PyQt5 import QtWidgets

from . import vmf

def open_vmf():
    vmf_browser = QtWidgets.QFileDialog()
    app = QtWidgets.QApplication.instance()
    mapsrc_dir = app.game_config.value("Hammer/MapDir")
    vmf_browser.setDirectory(mapsrc_dir)
    vmf_browser.setDefaultSuffix("vmf")
    vmf_path, ext = vmf_browser.getOpenFileName(filter="Valve Map Format (*.vmf)")
    if vmf_path == "": # no file was selected
        return False
    else:
        return vmf_path
