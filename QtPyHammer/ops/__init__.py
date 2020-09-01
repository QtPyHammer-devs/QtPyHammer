import os

from PyQt5 import QtWidgets

from . import vmf
from ..ui import workspace


def new_file(main_window):
    filename = "configs/blank.vmf"
    default_vmf_tab = workspace.VmfTab(filename, new=True, parent=main_window)
    main_window.tabs.addTab(default_vmf_tab, "untitled")

def open_files(main_window):
    open_dialog = QtWidgets.QFileDialog(main_window)
    app = QtWidgets.QApplication.instance()
    open_dialog.setDirectory(app.game_config.value("Hammer/MapDir"))
    # it may be better if the open_dialog remembered it's location when closed
    # finding yourself back at the start everytime you open could get frustrating
    filetype_filters = ["Valve Map Format (*.vmf)",
                        "QtPyHammer file (*.qph)",
                        "All files (*.*)"]
    open_dialog.setDefaultSuffix("vmf")
    filter_string = ";;".join(filetype_filters)
    filenames, active_filter = open_dialog.getOpenFileNames(filter=filter_string)
    for filename in filenames:
        raw_filename, extension = os.path.splitext(filename)
        short_filename = os.path.basename(filename)
        if extension == ".vmf":
            tab = workspace.VmfTab(filename, new=False, parent=main_window)
        elif extension == ".qph":
            raise NotImplementedError("No .qph viewport tabs yet")
            # tab = workspace.QphTab(filename, new=False, parent=main_window)
        main_window.tabs.addTab(tab, short_filename)

def save_file(main_window):
    """Save the file that is currently open"""
    assert main_window.tabs.currentIndex() != -1 # can active_tab be saved?
    active_tab = main_window.tabs.currentWidget()
    if active_tab.never_saved is True:
        save_file_as(main_window)
    else:
        active_tab.save_to_file()

def save_file_as(main_window):
    """Open a file browser and choose a location to save, then save"""
    assert main_window.tabs.currentIndex() != -1 # can active_tab be saved?
    active_tab = main_window.tabs.currentWidget()
    save_dialog = QtWidgets.QFileDialog(main_window)
    app = QtWidgets.QApplication.instance()
    save_dialog.setDirectory(app.game_config.value("Hammer/MapDir"))
    filetype_filters = ["Valve Map Format (*.vmf)",
                        "QtPyHammer file (*.qph)",
                        "All files (*.*)"]
    save_dialog.setDefaultSuffix("vmf")
    filter_string = ";;".join(filetype_filters)
    filename, active_filter = save_dialog.getSaveFileName(filter=filter_string)
    # ^ TEST save_dialog handles warnings (file extensions & saving over files)
    if filename == "":
        return # nowhere to save to, cancel saving
    active_tab.filename = filename # <- where to save
    active_tab.save_to_file()
    active_tab_index = main_window.tabs.currentIndex()
    raw_filename, extension = os.path.splitext(filename)
    short_filename = os.path.basename(filename)
    main_window.tabs.setTabText(active_tab_index, short_filename)

##def export(main_window):
##    # is the active file a .vmf? export .qph
##    # is the active file a .qph? export .vmf
##    # ^ the export action's text should reflect this (ui.core.MainWindow)
