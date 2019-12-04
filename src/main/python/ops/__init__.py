from PyQt5 import QtWidgets

from . import vmf

def open_vmf():
    vmf_browser = QtWidgets.QFileDialog() # cannot define widgets until after QApplication in main.py
    vmf_browser.setDirectory("F:/Modding/tf2 maps/") # default map directory
    vmf_browser.setDefaultSuffix("vmf") # for saving
    vmf_path, ext = vmf_browser.getOpenFileName(filter="Valve Map Format (*.vmf)")
    return vmf_path
