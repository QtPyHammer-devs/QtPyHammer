import sys

from PyQt5 import QtWidgets

sys.path.insert(0, "../")
from ui import map_tab
from utilities import solid, vector, vmf


def new_file(instance):
    """create new vmf/qph session object"""
    pass
    # could simply open blank.vmf

def new_tab(path, vmf_namespace, source_path=""):
    tab = map_tab.MapTab(vmf_namespace)
    tab.source_path = source_path
    # if not None, save to this path
    if source_path != "":
        tab.setTitle(source_path.rpatrition("/")[2])
    return tab

def open_vmf():
    vmf_browser = QtWidgets.QFileDialog() # cannot define widgets until after QApplication in main.py
    vmf_browser.setDirectory("F:/Modding/tf2 maps/") # default map directory
    vmf_browser.setDefaultSuffix("vmf") # for saving
    vmf_path, ext = vmf_browser.getOpenFileName(filter="Valve Map Format (*.vmf)")
    return vmf_path, vmf.namespace_from(vmf_path)

def import_vmf(path):
    """create a vmf/qph session object from a .vmf file"""
    vmf_file = open(path)
    return vmf.namespace_from(vmf_file) # a progress bar would be nice
