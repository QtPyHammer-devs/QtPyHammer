import sys
sys.path.insert(0, "../")
from utilities import solid, vector, vmf


def new_file(instance):
    """create new vmf/qph session object"""
    pass


def new_tab(instance):
    raise NotImplemented("Do it later, if at all")
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


# globals for open_file
vmf_browser = QtWidgets.QFileDialog()
vmf_browser.setDirectory('F:/Modding/tf2 maps/') # default map directory
vmf_browser.setDefaultSuffix('vmf') # for saving

def open_file(instance, vmf_file):
    """create a vmf/qph session object from a .vmf file"""
    vmf_path, ext = vmf_browser.getOpenFileName(filter='Valve Map Format (*.vmf)')
    # vmf_file = open(vmf_path)
    # convert vmf_file to useful a object in a thread seperate from UI
    # progress bar (but how?)
    # attach the object to the instance of QPH's MainWindow
