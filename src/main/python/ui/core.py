"""QtPyHammer MainWindow class & other core ui classes"""
import itertools
import sys
# Third-party imports
from PyQt5 import QtCore, QtGui, QtWidgets
import numpy as np
from OpenGL.GL import *
from OpenGL.GL.shaders import compileShader, compileProgram
from OpenGL.GLU import *
# QPH imports
from . import entity, viewport # ui
sys.path.insert(0, "../") # sibling packages
import ops # connects buttons to functions
from utilities import render

def except_hook(cls, exception, traceback): # nessecary for debugging SLOTS
    sys.__excepthook__(cls, exception, traceback)
sys.excepthook = except_hook


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None, ctx=None):
        super(QtWidgets.QMainWindow, self).__init__(parent)
        self.ctx = ctx # the fbs ApplicationContext

        ... # objects for holding map & session data
        self.actions = {} # {"identifier": action}
        # map all actions so we can rebind EVERYTHING
        self.open_vmf = ops.import_vmf(ctx.get_resource("vmfs/test2.vmf"))

        self.setTabPosition(QtCore.Qt.TopDockWidgetArea, QtWidgets.QTabWidget.North)
        self.main_menu = QtWidgets.QMenuBar()
        file_menu = self.main_menu.addMenu('&File')
        self.actions["File>New"] = file_menu.addAction('&New')
        self.actions["File>New"].setEnabled(False)
        #self.actions["File>New"].triggered.connect(ops.core.new_file)
        self.actions["File>Open"] = file_menu.addAction('&Open')
        def set_open_vmf(): # should really be in ops/__init__
            new_path = ops.open_vmf()
            print("Opening", new_path)
            self.open_vmf = new_path
            # connect to objects that hold vmf data for editing
            # maybe even make a new tab
            self.viewport.executeGL(render.vmf_setup, self.open_vmf, self.ctx)
        self.actions["File>Open"].triggered.connect(set_open_vmf)
        self.actions["File>Save"] = file_menu.addAction('&Save')
        self.actions["File>Save"].setEnabled(False)
        # opens browser on first save / save_as & otherwise is silent
##        self.actions["File>Save"].triggered.connect(ops.core.save_file)
        self.actions["File>Save As"] = file_menu.addAction('Save &As')
        self.actions["File>Save As"].setEnabled(False)
        # change args so save_file asks for a new location
##        self.actions["File>Save As"].triggered.connect(ops.core.save_file)
        file_menu.addSeparator()
##        self.import_menu = file_menu.addMenu('Import')
##        self.import_menu.addAction('.obj')
##        export_menu = file_menu.addMenu('Export')
##        export_menu.addAction('.obj')
##        export_menu.addAction('.smd')
##        file_menu.addSeparator()
        self.actions["File>Options"] = file_menu.addAction('&Options')
        self.actions["File>Options"].setEnabled(False)
##        self.actions["File>Options"].triggered.connect(ui.settings)
        file_menu.addSeparator()
        self.actions["File>Compile"] = file_menu.addAction('Compile')
        self.actions["File>Compile"].setEnabled(False)
##        self.actions["File>Compile"].triggered.connect(ui.compile)
        file_menu.addSeparator()
        self.actions["File>Exit"] = file_menu.addAction('Exit')
        self.actions["File>Exit"].triggered.connect(QtCore.QCoreApplication.quit)

        edit_menu = self.main_menu.addMenu('&Edit')
        self.actions["Edit>Undo"] = edit_menu.addAction('Undo')
        self.actions["Edit>Undo"].setEnabled(False)
##        self.actions["Edit>Undo"].triggered.connect( # edit timeline
        self.actions["Edit>Redo"] = edit_menu.addAction('Redo')
        self.actions["Edit>Redo"].setEnabled(False)
##        self.actions["Edit>Undo"].triggered.connect( # edit timeline
        self.actions["Edit>History"] = edit_menu.addMenu('&History...')
        self.actions["Edit>History"].setEnabled(False)
##        self.actions["Edit>History"].triggered.connect(ui.edit_timeline)
        edit_menu.addSeparator()
        self.actions["Edit>Find"] = edit_menu.addAction('Find &Entites')
        self.actions["Edit>Find"].setEnabled(False)
##        self.actions["Edit>Find"].triggered.connect(vmf.search)
        self.actions["Edit>Replace"] = edit_menu.addAction('&Replace')
        self.actions["Edit>Replace"].setEnabled(False)
##        self.actions["Edit>Replace"].triggered.connect(vmf.replace)
        edit_menu.addSeparator()
        self.actions["Edit>Cut"] = edit_menu.addAction('Cu&t')
        self.actions["Edit>Cut"].setEnabled(False)
##        self.actions["Edit>Cut"].triggered.connect(
        self.actions["Edit>Copy"] = edit_menu.addAction('&Copy')
        self.actions["Edit>Copy"].setEnabled(False)
##        self.actions["Edit>Copy"].triggered.connect(
        self.actions["Edit>Paste"] = edit_menu.addAction('&Paste')
        self.actions["Edit>Paste"].setEnabled(False)
##        self.actions["Edit>Paste"].triggered.connect(
        self.actions["Edit>Paste Special"] = edit_menu.addAction('Paste &Special')
        self.actions["Edit>Paste Special"].setEnabled(False)
##        self.actions["Edit>Paste Special"].triggered.connect(
        self.actions["Edit>Delete"] = edit_menu.addAction('&Delete')
        self.actions["Edit>Delete"].setEnabled(False)
##        self.actions["Edit>Delete"].triggered.connect(
        edit_menu.addSeparator()
        self.actions["Edit>Properties"] = edit_menu.addAction('P&roperties')
        self.actions["Edit>Properties"].setEnabled(False)
##        self.actions["Edit>Properties"].triggered.connect(

        tools_menu = self.main_menu.addMenu('&Tools')
        self.actions["Tools>Group"] = tools_menu.addAction('&Group')
        self.actions["Tools>Group"].setEnabled(False)
##        self.actions["Tools>Group"].triggered.connect(
        self.actions["Tools>Ungroup"] = tools_menu.addAction('&Ungroup')
        self.actions["Tools>Ungroup"].setEnabled(False)
##        self.actions["Tools>Ungroup"].triggered.connect(
        tools_menu.addSeparator()
        self.actions["Tools>Brush to Entity"] = tools_menu.addAction('&Tie to Entitiy')
        #self.actions["Tools>Brush to Entity"].setEnabled(False) # fbs .get_resource breaks fgd-tool
        ent_browser = entity.browser(self)
        self.actions["Tools>Brush to Entity"].triggered.connect(ent_browser.exec)
        self.actions["Tools>Entity to Brush"] = tools_menu.addAction('&Move to World')
        self.actions["Tools>Entity to Brush"].setEnabled(False)
##        self.actions["Tools>Entity to Brush"].triggered.connect(
        tools_menu.addSeparator()
        self.actions["Tools>Apply Texture"] = tools_menu.addAction('&Apply Texture')
        self.actions["Tools>Apply Texture"].setEnabled(False)
##        self.actions["Tools>Apply Texture"].triggered.connect(ops.texture.apply)
        self.actions["Tools>Replace Texture"] = tools_menu.addAction('&Replace Textures')
        self.actions["Tools>Replace Texture"].setEnabled(False)
##        self.actions["Tools>Replace Texture"].triggered.connect(ops.texture.replace)
        self.actions["Tools>Texture Lock"] = tools_menu.addAction('Texture &Lock')
        self.actions["Tools>Texture Lock"].setCheckable(True)
        self.actions["Tools>Texture Lock"].setEnabled(False)
##        self.actions["Tools>Texture Lock"].triggered.connect(
        tools_menu.addSeparator()
        self.actions["Tools>Sound Browser"] = tools_menu.addAction('&Sound Browser')
        self.actions["Tools>Sound Browser"].setEnabled(False)
##        self.actions["Tools>Sound Browser"].triggered.connect(ui.sound_browser)
        tools_menu.addSeparator()
        self.actions["Tools>Transform"] = tools_menu.addAction('Transform')
        self.actions["Tools>Transform"].setEnabled(False)
##        self.actions["Tools>Transform"].triggered.connect(
        self.actions["Tools>Snap to Grid"] = tools_menu.addAction('Snap Selection to Grid')
        self.actions["Tools>Snap to Grid"].setEnabled(False)
##        self.actions["Tools>Snap to Grid"].triggered.connect(
        tools_menu.addSeparator()
        self.actions["Tools>Flip Horizontally"] = tools_menu.addAction('Flip Horizontally')
        self.actions["Tools>Flip Horizontally"].setEnabled(False)
##        self.actions["Tools>Flip Horizontally"].triggered.connect(
        self.actions["Tools>Flip Vertically"] = tools_menu.addAction('Flip Vertically')
        self.actions["Tools>Flip Vertically"].setEnabled(False)
##        self.actions["Tools>Flip Vertically"].triggered.connect(
        tools_menu.addSeparator()
        self.actions["Tools>Create Prefab"] = tools_menu.addAction('&Create Prefab')
        self.actions["Tools>Create Prefab"].setEnabled(False)
##        self.actions["Tools>Create Prefab"].triggered.connect(

        map_menu = self.main_menu.addMenu('&Map')
        self.actions["Map>Snap to Grid"] = map_menu.addAction('&Snap to Grid')
        self.actions["Map>Snap to Grid"].setCheckable(True)
        self.actions["Map>Snap to Grid"].setChecked(True)
        self.actions["Map>Snap to Grid"].setEnabled(False)
##        self.actions["Map>Snap to Grid"].triggered.connect(
        self.actions["Map>Show Grid"] = map_menu.addAction('Sho&w Grid')
        self.actions["Map>Show Grid"].setCheckable(True)
        self.actions["Map>Show Grid"].setChecked(True)
        self.actions["Map>Show Grid"].setEnabled(False)
##        self.actions["Map>Show Grid"].triggered.connect(
        grid_settings = map_menu.addMenu('&Grid Settings')
        # Grid+ [
        # Grid- ]
        grid_settings.setEnabled(False)
        map_menu.addSeparator()
        self.actions["Map>Entity Report"] = map_menu.addAction('&Entity Report')
        self.actions["Map>Entity Report"].setEnabled(False)
##        self.actions["Map>Entity Report"].triggered.connect(ui.entity_report)
        #self.actions["Map>Zooify"] map_menu.addAction('&Zooify')
        # make an asset zoo / texture pallets from the currently open vmf
        self.actions["Map>Debug"] = map_menu.addAction('&Check for Problems')
        self.actions["Map>Debug"].setEnabled(False)
##        self.actions["Map>Debug"].triggered.connect(ui.map.debug)
        #map_menu.addAction('&Diff Map File')
        map_menu.addSeparator()
        self.actions["Map>Pointfile"] = map_menu.addAction('Pointfile / Find Leak (.lin)')
        self.actions["Map>Pointfile"].setEnabled(False)
##        self.actions["Map>Pointfile"].triggered.connect(
        self.actions["Map>Portal File"] = map_menu.addAction('Portal file (.prt)')
        self.actions["Map>Portal File"].setEnabled(False)
##        self.actions["Map>Portal File"].triggered.connect(
        map_menu.addSeparator()
        #map_menu.addAction('Show &Information')
        self.actions["Map>Properties"] = map_menu.addAction('&Map Properties')
        self.actions["Map>Properties"].setEnabled(False)
##        self.actions["Map>Properties"].triggered.connect(ui.map.properties)

        search_menu = self.main_menu.addMenu('&Search')
        self.actions["Search>Entity"] = search_menu.addAction('Find &Entity')
        self.actions["Search>Entity"].setEnabled(False)
##        self.actions["Search>Entity"].triggered.connect(ui.search.entity)
        self.actions["Search>Logic"] = search_menu.addAction('Find &IO')
        self.actions["Search>Logic"].setEnabled(False)
##        self.actions["Search>Logic"].triggered.connect(ui.search.logic)
        self.actions["Search>Replace Logic"] = search_menu.addAction('Find + &Replace IO')
        self.actions["Search>Replace Logic"].setEnabled(False)
##        self.actions["Search>Replace Logic"].triggered.connect(ui.search.logic)
        search_menu.addSeparator()
        self.actions["Search>Coords"] = search_menu.addAction('Go to &Coordinates')
        self.actions["Search>Coords"].setEnabled(False)
##        self.actions["Search>Coords"].triggered.connect(ui.search.coords)
        self.actions["Search>Brush"] = search_menu.addAction('Go to &Brush Number')
        self.actions["Search>Brush"].setEnabled(False)
##        self.actions["Search>Brush"].triggered.connect(ui.search.brush)

        view_menu = self.main_menu.addMenu('&View')
        self.actions["View>Center 2D"] = view_menu.addAction('Center 2D Views on selection')
        self.actions["View>Center 2D"].setEnabled(False)
##        self.actions["View>Center 2D"].triggered.connect(
        self.actions["View>Center 3D"] = view_menu.addAction('Center 3D Views on selection')
        self.actions["View>Center 3D"].setEnabled(False)
##        self.actions["View>Center 3D"].triggered.connect(
        view_menu.addAction(self.actions["Search>Coords"])
        view_menu.addSeparator()
        #self.actions["View>Logic"] = view_menu.addAction('Show &Logic Connections')
        #self.actions["View>Logic"].setCheckable(True)
        self.actions["View>Models"] = view_menu.addAction('Show &Models in 2D')
        self.actions["View>Models"].setCheckable(True)
        self.actions["View>Models"].setChecked(True)
        self.actions["View>Models"].setEnabled(False)
##        self.actions["View>Models"].triggered.connect(
        self.actions["View>Entity Names"] = view_menu.addAction('Entity &Names')
        self.actions["View>Entity Names"].setCheckable(True)
        self.actions["View>Entity Names"].setChecked(True)
        self.actions["View>Entity Names"].setEnabled(False)
##        self.actions["View>Entity Names"].triggered.connect(
        self.actions["View>Radius Culling"] = view_menu.addAction('Radius &Culling')
        self.actions["View>Radius Culling"].setCheckable(True)
        self.actions["View>Radius Culling"].setChecked(True)
        self.actions["View>Radius Culling"].setEnabled(False)
##        self.actions["View>Radius Culling"].triggered.connect(
        view_menu.addSeparator()
        self.actions["View>Hide"] = view_menu.addAction('&Hide')
        self.actions["View>Hide"].setEnabled(False)
##        self.actions["View>Hide"].triggered.connect(
        self.actions["View>Hide Unselected"] = view_menu.addAction('&Hide Unselected')
        self.actions["View>Hide Unselected"].setEnabled(False)
##        self.actions["View>Hide Unselected"].triggered.connect(
        self.actions["View>Unhide"] = view_menu.addAction('&Unhide')
        self.actions["View>Unhide"].setEnabled(False)
##        self.actions["View>Unhide"].triggered.connect(
        view_menu.addSeparator()
        self.actions["View>Visgroups"] = view_menu.addAction('Move Selection to Visgroup')
        self.actions["View>Visgroups"].setEnabled(False)
##        self.actions["View>Visgroups"].triggered.connect(ui.
        view_menu.addSeparator()
        self.actions["View>Settings"] = view_menu.addAction('&OpenGL Settings')
        self.actions["View>Settings"].setEnabled(False)
##        self.actions["View>Settings"].triggered.connect(ui.

        open_url = lambda url: lambda: QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))
        help_menu = self.main_menu.addMenu('&Help')
        self.actions["Help>Offline"] = help_menu.addAction('Offline Help')
        self.actions["Help>Offline"].setEnabled(False)
##        self.actions["Help>Offline"].triggered.connect(ui.
        help_menu.addSeparator()
        self.actions["Help>About QPH"] = help_menu.addAction('About QtPyHammer')
        self.actions["Help>About QPH"].triggered.connect(
            open_url("https://github.com/snake-biscuits/QtPyHammer"))
        self.actions["Help>About Qt"] = help_menu.addAction('About Qt')
        self.actions["Help>About Qt"].setEnabled(False)
##        self.actions["Help>About Qt"].triggered.connect(ui.
        self.actions["Help>Liscense"] = help_menu.addAction('License')
        self.actions["Help>Liscense"].setEnabled(False)
##        self.actions["Help>Liscense"].triggered.connect(ui.
        self.actions["Help>Contributors"] = help_menu.addAction('Contributors')
        self.actions["Help>Contributors"].setEnabled(False)
##        self.actions["Help>Contributors"].triggered.connect(ui.
        help_menu.addSeparator()
        self.actions["Help>VDC"] = help_menu.addAction('Valve Developer Community')
        self.actions["Help>VDC"].triggered.connect(
            open_url("https://developer.valvesoftware.com/wiki/Main_Page"))
        self.actions["Help>TF2Maps"] = help_menu.addAction('TF2Maps.net')
        self.actions["Help>TF2Maps"].triggered.connect(
            open_url("https://tf2maps.net"))

        # use QSettings instead
        line_no = 0
        for line in open(self.ctx.get_resource("configs/core_binds.txt")):
            line_no += 1
            line = line.rstrip("\r\n")
            if line == "":
                continue
            try:
                action, shortcut = line.split(" " * 4)
            except Exception as exc:
                print(line_no, "|{}|".format(line), "is not formatted correctly")
            try:
                self.actions[action].setShortcut(shortcut)
            except AttributeError:
                print(action, "is not a registered action")

        self.setMenuBar(self.main_menu)

##        # TOOLBARS
##        key_tools = QtWidgets.QToolBar('Tools 1')
##        key_tools.setMovable(False)
##        button_1 = QtWidgets.QToolButton() # need icons (.png)
##        button_1.setToolTip('Toggle 2D grid visibility')
##        key_tools.addWidget(button_1)
##        button_2 = QtWidgets.QToolButton()
##        button_2.setToolTip('Toggle 3D grid visibility')
##        key_tools.addWidget(button_2)
##        button_3 = QtWidgets.QToolButton()
##        button_3.setToolTip('Grid scale -  [')
##        key_tools.addWidget(button_3)
##        button_3 = QtWidgets.QToolButton()
##        button_3.setDefaultAction(...) # shortcut ']'
##        key_tools.addWidget(button_3)
##        key_tools.addSeparator()

        # self.addToolBar(QtCore.Qt.TopToolBarArea, key_tools)
        # # undo redo | carve | group ungroup ignore | hide unhide alt-hide |
        # # cut copy paste | cordon radius | TL <TL> | DD 3D DW DA |
        # # compile helpers 2D_models fade CM prop_detail NO_DRAW

        self.viewport = viewport.Viewport3D(60)
        self.setCentralWidget(self.viewport)
        self.viewport.setFocus()

    def viewport_setup(self):
        self.viewport.sharedGLsetup() # setup shared GLcontexts
        self.viewport.executeGL(render.vmf_setup, self.open_vmf, self.ctx)

    def show(self):
        super(MainWindow, self).show()
        self.viewport_setup()

    def showMaximized(self):
        super(MainWindow, self).showMaximized()
        self.viewport_setup()
