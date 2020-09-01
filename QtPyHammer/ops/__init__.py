import os
import sys

from PyQt5 import QtCore, QtWidgets

from . import vmf
from ..ui import workspace


class map_file_browser(QtWidgets.QFileDialog):
    def __init__(self, parent):
        super(QtWidgets.QFileDialog, self).__init__(parent)
        if sys.platform == "linux":
            # GtkDialog mapped without a transient parent. This is discouraged.
            self.setOption(self.Option.DontUseNativeDialog) # no apparent effect
        app = QtWidgets.QApplication.instance() 
        self.setDirectory(app.game_config.value("Hammer/MapDir"))
        self.setNameFilters(["Valve Map Format (*.vmf)",
                            "QtPyHammer file (*.qph)",
                            "All files (*.*)"])
        self.setDefaultSuffix("vmf")


def new_file(main_window):
    filename = "configs/blank.vmf"
    default_vmf_tab = workspace.VmfTab(filename, new=True, parent=main_window)
    main_window.tabs.addTab(default_vmf_tab, "untitled")

def open_files(main_window, open_dialog):    
    filenames, active_filter = open_dialog.getOpenFileNames(parent=main_window, caption="Open...")
    for filename in filenames:
        raw_filename, extension = os.path.splitext(filename)
        short_filename = os.path.basename(filename)
        if extension == ".vmf":
            tab = workspace.VmfTab(filename, new=False, parent=main_window)
        elif extension == ".qph":
            raise NotImplementedError("No .qph viewport tabs yet")
            # tab = workspace.QphTab(filename, new=False, parent=main_window)
        main_window.tabs.addTab(tab, short_filename)

def save_file(main_window, save_dialog):
    """Save the file that is currently open"""
    if main_window.tabs.currentIndex() != -1:
        return # nothing to save
    active_tab = main_window.tabs.currentWidget()
    if active_tab.never_saved is True:
        save_file_as(main_window, save_dialog)
    else:
        active_tab.save_to_file()

def save_file_as(main_window, save_dialog):
    """Open a file browser and choose a location to save, then save"""
    if main_window.tabs.currentIndex() != -1:
        return # nothing to save
    active_tab = main_window.tabs.currentWidget()
    filename, active_filter = save_dialog.getSaveFileName(parent=main_window, caption="Save...")
    # ^ TEST save_dialog handles warnings (file extensions & saving over files)
    if filename == "":
        return # nowhere to save to, cancel saving
    active_tab.filename = filename
    active_tab.save_to_file()
    active_tab_index = main_window.tabs.currentIndex()
    raw_filename, extension = os.path.splitext(filename)
    short_filename = os.path.basename(filename)
    main_window.tabs.setTabText(active_tab_index, short_filename)

##def export(main_window):
##    # is the active file a .vmf? export .qph
##    # is the active file a .qph? export .vmf
##    # ^ the export action's text should reflect this (ui.core.MainWindow)
