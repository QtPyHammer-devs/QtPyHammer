import os

from PyQt5 import QtWidgets

from . import vmf


current_dir = os.path.dirname(os.path.realpath(__file__))

def open_vmf():
    vmf_browser = QtWidgets.QFileDialog()
    mapsrc_dir = os.path.join(current_dir, "../../test_maps/")
    vmf_browser.setDirectory(mapsrc_dir)
    vmf_browser.setDefaultSuffix("vmf")
    vmf_path, ext = vmf_browser.getOpenFileName(filter="Valve Map Format (*.vmf)")
    if vmf_path == "": # no file was selected
        return False
    else:
        return vmf_path
