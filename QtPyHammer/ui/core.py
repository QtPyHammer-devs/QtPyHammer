"""QtPyHammer MainWindow class & other core ui classes"""
from __future__ import annotations
import os
from typing import Callable, Dict, Union

from PyQt5 import QtCore, QtGui, QtWidgets

from .. import ops
from ..ui import entity
from ..ui import workspace


def add_action(
    menu: QtWidgets.QAction,
    label: str,
    func: Union[None, Callable[None, None]] = None,
    enabled: bool = True,
    checked: Union[None, bool] = None,
) -> QtWidgets.QAction:
    """general action setup"""
    action = menu.addAction(label)
    if func is not None:
        action.triggered.connect(func)
    if func is None or enabled is False:
        action.setEnabled(False)
    if checked in (True, False):
        action.setCheckable(True)
        action.setChecked(checked)
    return action


class MainWindow(QtWidgets.QMainWindow):
    """The Main Map Editor Window"""
    actions: Dict[str, QtWidgets.QAction]
    # ^ {"identifier": action}
    main_menu: QtWidgets.QMenuBar
    map_browser: ops.MapFileBrowser
    tabs: QtWidgets.QTabWidget

    def __init__(self, parent=None):
        super(QtWidgets.QMainWindow, self).__init__(parent)
        # make window
        self.setWindowTitle("QtPyHammer")
        self.setMinimumSize(640, 480)

        # dialogs
        self.map_browser = ops.MapFileBrowser(self)

        # tabs
        self._init_tabs()

        # toolbars
        self._init_toolbars()

        # menus
        self.actions = dict()
        # TODO: separate into classes?
        # -- some actions need to be disabled if no map is open
        # TODO: link actions to current map tab
        self.main_menu = QtWidgets.QMenuBar()
        self._init_file_menu()
        self._init_edit_menu()
        self._init_tools_menu()
        self._init_map_menu()
        self._init_search_menu()
        self._init_view_menu()
        self._init_help_menu()

        # attach all actions to hotkeys
        app = QtWidgets.QApplication.instance()
        for action in app.hotkeys.allKeys():
            if not action.startswith("Menu."):
                # TODO: filter w/ some QSettings feature? (not .allKeys())
                continue
            action_name = action[5:]  # remove leading "Menu."
            if action_name not in self.actions:
                continue
            shortcut = app.hotkeys.value(action)
            self.actions[action_name].setShortcut(shortcut)

        self.setMenuBar(self.main_menu)

    def _init_file_menu(self):
        file_menu = self.main_menu.addMenu("&File")
        # file operations
        self.actions["File/New"] = add_action(
            file_menu, "&New",
            func=lambda: ops.new_file(self))
        self.actions["File/Open"] = add_action(
            file_menu, "&Open",
            func=lambda: ops.open_files(self, self.map_browser))
        # TODO: Open Recent
        self.actions["File/Save"] = add_action(
            file_menu, "&Save",
            func=lambda: ops.save_file(self, self.map_browser))
        self.actions["File/Save As"] = add_action(
            file_menu, "Save &As",
            func=lambda: ops.save_file_as(self, self.map_browser))
        # file_menu.addSeparator()  # import / export
        # TODO: import / export reference models etc.
        # import_menu = file_menu.addMenu("Import")
        # import_menu.addAction(".obj")
        # export_menu = file_menu.addMenu("Export")
        # export_menu.addAction("Prefab")
        # export_menu.addAction(".qph") # grayed out if active tab is a .qph
        # export_menu.addAction(".obj")
        # export_menu.addAction(".smd")
        file_menu.addSeparator()  # compile
        self.actions["File/Compile"] = add_action(
            file_menu, "Compile")
        # TODO: func=ui.compile)
        file_menu.addSeparator()  # exit
        self.actions["File/Exit"] = add_action(
            file_menu, "Exit",
            func=QtCore.QCoreApplication.quit)

    def _init_edit_menu(self):
        edit_menu = self.main_menu.addMenu("&Edit")
        # edit history
        self.actions["Edit/Undo"] = add_action(
            edit_menu, "Undo")
        # TODO: edit_timeline.undo
        self.actions["Edit/Redo"] = add_action(
            edit_menu, "Redo")
        # TODO: edit_timeline.redo
        self.actions["Edit/History"] = add_action(
            edit_menu, "&History...")
        # TODO: edit_timeline.open_dialog
        edit_menu.addSeparator()
        # search & replace
        self.actions["Edit/Find"] = add_action(
            edit_menu, "Find &Entites")
        # TODO: open a search dialog
        self.actions["Edit/Replace"] = add_action(
            edit_menu, "&Replace")
        # TODO: open a find & replace dialog
        edit_menu.addSeparator()

        self.actions["Edit/Cut"] = edit_menu.addAction("Cu&t")
        self.actions["Edit/Cut"].setEnabled(False)
        # self.actions["Edit/Cut"].triggered.connect(

        self.actions["Edit/Copy"] = edit_menu.addAction("&Copy")
        self.actions["Edit/Copy"].setEnabled(False)
        # self.actions["Edit/Copy"].triggered.connect(

        self.actions["Edit/Paste"] = add_action(
            edit_menu, "&Paste")
        # TODO: paste action
        self.actions["Edit/Paste Special"] = add_action(
            edit_menu, "Paste &Special")
        # TODO: paste_special dialog
        self.actions["Edit/Delete"] = add_action(
            edit_menu, "&Delete")
        # TODO: delete selection
        edit_menu.addSeparator()
        # options
        self.actions["Edit/Preferences"] = add_action(
            edit_menu, "Preferences")
        # TODO: func=ui.settings)

    def _init_tools_menu(self):
        tools_menu = self.main_menu.addMenu("&Tools")
        self.actions["Tools/Group"] = add_action(
            tools_menu, "&Group")
        self.actions["Tools/Ungroup"] = add_action(
            tools_menu, "&Ungroup")
        tools_menu.addSeparator()
        # world / entity brush conversion
        self.actions["Tools/Brush to Entity"] = add_action(
            tools_menu, "&Tie to Entitiy")
        # TODO: get this mess outta here
        try:
            ent_browser = entity.Editor(parent=self)
            self.actions["Tools/Brush to Entity"].triggered.connect(
                ent_browser.show)
        except Exception as exc:
            print("Failed to load .fgds!")  # TODO: log instead of printing
            self.actions["Tools/Brush to Entity"].setEnabled(False)
            raise exc

        self.actions["Tools/Entity to Brush"] = add_action(
            tools_menu, "&Move to World")
        tools_menu.addSeparator()
        self.actions["Tools/Apply Texture"] = add_action(
            tools_menu, "&Apply Texture")
        # TODO: func=ops.texture.apply)
        self.actions["Tools/Replace Texture"] = add_action(
            tools_menu, "&Replace Textures")
        # TODO: func=ops.texture.replace)
        self.actions["Tools/Texture Lock"] = add_action(
            tools_menu, "Texture &Lock", checked=False)
        # TODO: enable / disable texture lock
        tools_menu.addSeparator()  # sound browser
        self.actions["Tools/Sound Browser"] = add_action(
            tools_menu, "&Sound Browser")
        # TODO: func=ui.browse.sounds)
        tools_menu.addSeparator()  # 2D transforms
        self.actions["Tools/Transform"] = add_action(
            tools_menu, "Transform")
        # TODO: transform dialog?
        self.actions["Tools/Snap Selection to Grid"] = add_action(
            tools_menu, "Snap Selection to Grid")
        # TODO: func=...
        tools_menu.addSeparator()  # flip
        self.actions["Tools/Flip Horizontally"] = add_action(
            tools_menu, "Flip Horizontally")
        # TODO: func=...
        self.actions["Tools/Flip Vertically"] = add_action(
            tools_menu, "Flip Vertically")
        # TODO: func=...
        tools_menu.addSeparator()  # prefabs
        self.actions["Tools/Create Prefab"] = add_action(
            tools_menu, "Create &Prefab")

    def _init_map_menu(self):
        map_menu = self.main_menu.addMenu("&Map")
        self.actions["Map/Snap to Grid"] = add_action(
            map_menu, "&Snap to Grid",
            checked=True)
        # TODO: func=...
        self.actions["Map/Show Grid"] = add_action(
            map_menu, "Sho&w Grid",
            checked=True)
        # TODO: func=...

        grid_settings = map_menu.addMenu("&Grid Settings")
        # TODO: Grid+ [
        # TODO: Grid- ]
        grid_settings.setEnabled(False)

        map_menu.addSeparator()  # entity report
        self.actions["Map/Entity Report"] = add_action(
            map_menu, "&Entity Report")
        # TODO: func=ui.entity_report)
        self.actions["Map/Zooify"] = add_action(
            map_menu, "&Zooify")
        # TODO: make an asset zoo / texture palette image from the current file
        self.actions["Map/Debug"] = add_action(
            map_menu, "&Check for Problems")
        # TODO: func=ui.map.debug_dialog)
        self.actions["Map/Diff"] = add_action(
            map_menu, "&Diff Map File")
        # TODO: compare against another map file & show the difference
        map_menu.addSeparator()
        # VIS overlays
        self.actions["Map/Pointfile"] = add_action(
            map_menu, "Pointfile / Find Leak (.lin)")
        # TODO: browse for & load point file
        self.actions["Map/Portal File"] = add_action(
            map_menu, "Portal file (.prt)")
        # TODO: browse for & load portal file
        map_menu.addSeparator()
        # map info
        self.actions["Map/Information"] = add_action(
            map_menu, "Show &Information")
        # TODO: func=ui.map.info_dialog)
        self.actions["Map/Properties"] = add_action(
            map_menu, "&Map Properties")
        # TODO: func=ui.map.properties_editor)

    def _init_search_menu(self):
        search_menu = self.main_menu.addMenu("&Search")
        self.actions["Search/Entity"] = add_action(
            search_menu, "Find &Entity")
        # TODO: func=ui.search.entity)
        self.actions["Search/Logic"] = add_action(
            search_menu, "Find &IO")
        # TODO: func=ui.search.logic)
        self.actions["Search/Replace Logic"] = add_action(
            search_menu, "Find + &Replace IO")
        # TODO: func=ui.search.logic)
        search_menu.addSeparator()  # go to ...
        self.actions["Search/Coords"] = add_action(
            search_menu, "Go to &Coordinates")
        # TODO: func=ui.search.coords)
        self.actions["Search/Brush"] = add_action(
            search_menu, "Go to &Brush Number")
        # TODO: func=ui.search.brush)

    def _init_view_menu(self):
        view_menu = self.main_menu.addMenu("&View")
        self.actions["View/Center 2D"] = add_action(
            view_menu, "Center 2D Views on selection")
        # TODO: func=...
        self.actions["View/Center 3D"] = add_action(
            view_menu, "Center 3D Views on selection")
        # TODO: func=...
        view_menu.addAction(self.actions["Search/Coords"])  # copy
        view_menu.addSeparator()
        self.actions["View/Logic"] = add_action(
            view_menu, "Show &Logic Connections",
            checked=False)
        # TODO: func=...
        self.actions["View/Models"] = add_action(
            view_menu, "Show &Models in 2D",
            checked=True)
        # TODO: func=...
        self.actions["View/Entity Names"] = add_action(
            view_menu, "Entity &Names",
            checked=True)
        # TODO: func=...
        view_menu.addSeparator()  # hide / unhide
        self.actions["View/Hide"] = add_action(
            view_menu, "&Hide")
        # TODO: func=...
        self.actions["View/Hide Unselected"] = add_action(
            view_menu, "&Hide Unselected")
        # TODO: func=...
        self.actions["View/Unhide"] = add_action(
            view_menu, "&Unhide")
        # TODO: func=...
        view_menu.addSeparator()  # visgroups
        self.actions["View/Visgroups"] = add_action(
            view_menu, "Move Selection to Visgroup")
        # TODO: func=...  # spawn a dialog box
        view_menu.addSeparator()  # viewport settings
        self.actions["View/Settings"] = add_action(
            view_menu, "&OpenGL Settings")
        # TODO: func=...  # spawn a dialog box

    def _init_help_menu(self):
        open_url = QtGui.QDesktopServices.openUrl
        help_menu = self.main_menu.addMenu("&Help")
        self.actions["Help/Offline"] = add_action(
            help_menu, "Offline Help")
        # TODO: func=...  # open fgd help browser
        help_menu.addSeparator()  # about
        self.actions["Help/About QPH"] = add_action(
            help_menu, "About QtPyHammer",
            func=lambda: open_url(QtCore.QUrl(
                "https://github.com/snake-biscuits/QtPyHammer/wiki")))
        # TODO: func=...  # spawn a dialog box
        self.actions["Help/About Qt"] = add_action(
            help_menu, "About Qt")
        # TODO: func=...  # spawn a dialog box
        self.actions["Help/License"] = add_action(
            help_menu, "License")
        # TODO: func=...  # spawn a dialog box
        self.actions["Help/Contributors"] = add_action(
            help_menu, "Contributors")
        # TODO: func=...  # spawn a dialog box
        help_menu.addSeparator()  # web links
        self.actions["Help/VDC"] = add_action(
            help_menu, "Valve Developer Community",
            func=lambda: open_url(QtCore.QUrl(
                "https://developer.valvesoftware.com/wiki/Main_Page")))
        self.actions["Help/TF2Maps"] = add_action(
            help_menu, "TF2Maps.net",
            func=lambda: open_url(QtCore.QUrl("https://tf2maps.net")))

    def _init_toolbars(self):
        # TODO: icons (.svg?)
        key_tools = QtWidgets.QToolBar("Grid Tools")
        key_tools.setMovable(False)

        button_1 = QtWidgets.QToolButton()
        button_1.setToolTip("Toggle 2D Grid")
        key_tools.addWidget(button_1)

        button_2 = QtWidgets.QToolButton()
        button_2.setToolTip("Toggle 3D Grid")
        key_tools.addWidget(button_2)

        button_3 = QtWidgets.QToolButton()
        button_3.setToolTip("Grid Scale +")
        key_tools.addWidget(button_3)

        button_4 = QtWidgets.QToolButton()
        button_4.setToolTip("Grid Scale -")
        key_tools.addWidget(button_4)

        # key_tools.addSeparator()
        # undo redo | carve | group ungroup ignore | hide unhide alt-hide |
        # cut copy paste | cordon | TL <TL> | DD 3D DW DA |
        # compile helpers 2D_models fade CM prop_detail NO_DRAW

        self.addToolBar(QtCore.Qt.TopToolBarArea, key_tools)

    def _init_tabs(self):
        self.setTabPosition(
            QtCore.Qt.TopDockWidgetArea,
            QtWidgets.QTabWidget.North)
        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.tabs.removeTab)
        self.setCentralWidget(self.tabs)

    def open(self, filename):  # allows loading via drag & drop
        raw_filename, extension = os.path.splitext(filename)
        short_filename = os.path.basename(filename)
        if extension == ".vmf":
            tab = workspace.VmfTab(filename, new=False, parent=self)
        elif extension == ".qph":
            raise NotImplementedError("No .qph viewport tabs yet")
            # tab = workspace.QphTab(filename, new=False, parent=self)
        else:
            raise RuntimeError(f"{filename} is not a .vmf file")
        self.tabs.addTab(tab, short_filename)
        self.tabs.setCurrentIndex(self.tabs.count() - 1)
