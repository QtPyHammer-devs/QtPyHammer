import os
import sys

from PyQt5 import QtWidgets

from ..ui import workspace


filename_filters = ["Valve Map Format (*.vmf)",
                    "QtPyHammer file (*.qph)",
                    "All files (*.*)"]

# TODO: write a common function for detecting if files / folders exist
# - generate folders, with an optional popup
# - suggest close matches


class MapFileBrowser(QtWidgets.QFileDialog):
    def __init__(self, parent):
        super(QtWidgets.QFileDialog, self).__init__(parent)
        app = QtWidgets.QApplication.instance()
        self.setDirectory(app.game_config.value("Hammer/MapDir"))
        self.setNameFilters(filename_filters)
        # ^ is ignored by methods?
        self.setDefaultSuffix("vmf")


def new_file(main_window):
    filename = "configs/blank.vmf"
    default_vmf_tab = workspace.VmfTab(filename, new=True, parent=main_window)
    main_window.tabs.addTab(default_vmf_tab, "untitled")
    main_window.tabs.setCurrentIndex(main_window.tabs.count() - 1)


def open_files(main_window, open_dialog):
    kwargs = {"parent": main_window, "caption": "Open...",
              "filter": ";;".join(filename_filters)}
    if sys.platform == "linux":
        kwargs["options"] = open_dialog.Option.DontUseNativeDialog
    filenames, active_filter = open_dialog.getOpenFileNames(**kwargs)
    for filename in filenames:
        main_window.open(filename)


def save_file(main_window, save_dialog):
    """Save the file that is currently open"""
    if main_window.tabs.currentIndex() != -1:
        return  # nothing to save
    active_tab = main_window.tabs.currentWidget()
    if active_tab.never_saved is True:
        save_file_as(main_window, save_dialog)
    else:
        active_tab.save_to_file()


def save_file_as(main_window, save_dialog):
    """Open a file browser and choose a location to save, then save"""
    if main_window.tabs.currentIndex() == -1:
        return  # nothing to save
    active_tab = main_window.tabs.currentWidget()
    kwargs = {"parent": main_window, "caption": "Save...",
              "filter": ";;".join(filename_filters)}
    if sys.platform == "linux":
        kwargs["options"] = save_dialog.Option.DontUseNativeDialog
    filename, active_filter = save_dialog.getSaveFileName(**kwargs)
    # ^ TEST save_dialog handles warnings (file extensions & saving over files)
    if filename == "":
        return  # nowhere to save to, cancel saving
    active_tab.filename = filename
    active_tab.save_to_file()
    active_tab_index = main_window.tabs.currentIndex()
    raw_filename, extension = os.path.splitext(filename)
    short_filename = os.path.basename(filename)
    main_window.tabs.setTabText(active_tab_index, short_filename)

# TODO: export functions
# what is being exported? selection or file
# selection_to_X  (.mdl, .obj, .glTF, .fbx, .blend)
# map_to_X (.qph, .vmf, .obj, .blend)
# TODO: determine if a path to blender would be enough to generate .blends
