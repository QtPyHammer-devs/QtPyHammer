import sys

from PyQt5 import QtWidgets

sys.path.insert(0, "../")
from utilities import solid, vector, vmf


def new_file(instance):
    """create new vmf/qph session object"""
    pass
    # could simply open blank.vmf

def new_tab(instance):
    raise NotImplemented("haven't quite figured this out yet")
##    tabs = [] # Firefox-esque tabs that you can drag around
##              # (peel off to make a new window!)
##    new_file_count = 0
##    def new_tab(vmf=None): # add a new viewport
##        global new_file_count, window, tabs
##        new_file_count += 1
##        map_dock = viewports.QuadViewportDock(f'untitled {new_file_count}') # feed in vmf here
##        tabs.append(map_dock)
##        window.addDockWidget(QtCore.Qt.TopDockWidgetArea, map_dock)
##        # add dock as tab if already have one dock ?
##        map_dock.widget().layout().itemAt(2).widget().sharedGLsetup() # too soon

def open_vmf():
    vmf_browser = QtWidgets.QFileDialog() # cannot define widgets until after QApplication in main.py
    vmf_browser.setDirectory('F:/Modding/tf2 maps/') # default map directory
    vmf_browser.setDefaultSuffix('vmf') # for saving
    vmf_path, ext = vmf_browser.getOpenFileName(filter='Valve Map Format (*.vmf)')
    return import_vmf(vmf_path)

def import_vmf(path):
    """create a vmf/qph session object from a .vmf file"""
    vmf_file = open(path)
    return vmf.namespace_from(vmf_file) # a progress bar would be nice
