import sys
from PyQt5 import QtCore, QtGui, QtWidgets
import viewports


def print_methods(obj, filter_lambda=lambda x: True, joiner='\n'):
    methods = [a for a in dir(obj) if hasattr(getattr(obj, a), '__call__')]
    print(joiner.join([m for m in methods if filter_lambda(m) == True]))

# TODOS:
# context menu (set shortcut)
# clearly log & report crashes!
# especially those that occur in slots (sys.excepthook)
# vmf manager
# edit vmf as text (text editor)
# IDE (colours, auto-complete) preserve solids
# use IDE tools to attempt recovery of corrupt vmfs
# recovery tools in general

new_file_count = 0

# disable menu items when they cannot be used

# need a QSettings to store: LOAD HERE!
#  recent files
#  OpenGL settings
#  game configurations
#  default filepaths
#  keybinds
#  ...
# .ini should be straightforward enough

QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts)
app = QtWidgets.QApplication(sys.argv)
window = QtWidgets.QMainWindow()
window.setWindowTitle('QtPyHammer')
window.setGeometry(640, 400, 640, 480)
window.setTabPosition(QtCore.Qt.TopDockWidgetArea, QtWidgets.QTabWidget.North)

# read .fgd(s) for entity_data
# prepare .vpks (grab directories)
# mount custom data (tf/custom etc)

### MAIN MENU ###
menu = QtWidgets.QMenuBar()

file_menu = menu.addMenu('&File')
new_file = file_menu.addAction('&New')
new_file.setShortcut('Ctrl+N')

tabs = []
def new_tab(vmf=None): # add a new viewport
    global new_file_count, window, tabs
    new_file_count += 1
    map_dock = viewports.QuadViewportDock(f'untitled {new_file_count}') # feed in vmf here
    tabs.append(map_dock)
    window.addDockWidget(QtCore.Qt.TopDockWidgetArea, map_dock)
    # add dock as tab if already have one dock ?
##    map_dock.widget().layout().itemAt(2).widget().sharedGLsetup() # too soon
    
new_file.triggered.connect(new_tab) # also need to load .vmf into the manager

open_file = file_menu.addAction('&Open')
open_file.setShortcut('Ctrl+O')
open_browser = QtWidgets.QFileDialog()
open_browser.setDirectory('F:/Modding/tf2 maps/') # default map directory
open_browser.setDefaultSuffix('vmf') # for saving, doesn't filter
# set to open file and filter for .vmf

def load_vmf():
    vmf_name = QtWidgets.QFileDialog.getOpenFileName(filter='Valve Map Format (*.vmf)')[0]
    # load on a seoerate thread from ui
    # progress bar
    #   how do we measure progress when we don't have a value for 100% ?
    # reuse new_tab
    print(vmf_name)

open_file.triggered.connect(load_vmf)

file_menu.addAction('&Save').setShortcut('Ctrl+S')
file_menu.addAction('Save &As').setShortcut('Ctrl+Shift+S')
file_menu.addSeparator()
import_menu = file_menu.addMenu('Import')
import_menu.addAction('.obj')
import_menu.addAction('.blend')
export_menu = file_menu.addMenu('Export')
export_menu.addAction('.obj')
export_menu.addAction('.blend')
file_menu.addSeparator()
file_menu.addAction('&Options')
file_menu.addSeparator()
file_menu.addAction('Compile').setShortcut('F9')
file_menu.addSeparator()
file_menu.addAction('Exit')

edit_menu = menu.addMenu('&Edit')
edit_menu.addAction('Undo').setShortcut('Ctrl+Z')
edit_menu.addAction('Redo').setShortcut('Ctrl+Y')
edit_menu.addMenu('&History...')
edit_menu.addSeparator()
edit_menu.addAction('Find &Entites').setShortcut('Ctrl+Shift+F')
edit_menu.addAction('&Replace').setShortcut('Ctrl+Shift+R')
edit_menu.addSeparator()
edit_menu.addAction('Cu&t').setShortcut('Ctrl+X')
edit_menu.addAction('&Copy').setShortcut('Ctrl+C')
edit_menu.addAction('&Paste').setShortcut('Ctrl+V')
edit_menu.addAction('Paste &Special').setShortcut('Ctrl+Shift+V')
edit_menu.addAction('&Delete').setShortcut('Del')
edit_menu.addSeparator()
edit_menu.addAction('P&roperties').setShortcut('Alt+Enter')

map_menu = menu.addMenu('&Map')
snap_to_grid = map_menu.addAction('&Snap to Grid')
snap_to_grid.setShortcut('Shift+W')
snap_to_grid.setCheckable(True)
snap_to_grid.setChecked(True)
show_grid = map_menu.addAction('Sho&w Grid')
show_grid.setShortcut('Shift+R')
show_grid.setCheckable(True)
show_grid.setChecked(True)
grid_settings = map_menu.addMenu('&Grid Settings')
map_menu.addSeparator()
map_menu.addAction('&Entity Report')
map_menu.addAction('&Zooify') # make an asset zoo / texture pallets
map_menu.addAction('&Check for Problems').setShortcut('Alt+P')
map_menu.addAction('&Diff Map File')
map_menu.addSeparator()
map_menu.addAction('Find Leak (.lin)')
map_menu.addAction('Portalfile (.prt)')
map_menu.addSeparator()
map_menu.addAction('Show &Information')
map_menu.addAction('&Map Properties') # skybox / detail file

search_menu = menu.addMenu('&Search')
search_menu.addAction('Find Entity')
search_menu.addAction('Find IO')
search_menu.addAction('Find + Replace IO')
search_menu.addSeparator()
search_menu.addAction('Goto Coordinates')

view_menu = menu.addMenu('&View')
view_menu.addAction('Add &Viewport')
view_menu.addSeparator()
view_menu.addAction('Center 2D Views on selection').setShortcut('Ctrl+E')
view_menu.addAction('Center 3D Views on selection').setShortcut('Ctrl+Shift+E')
view_menu.addAction('Go To &Coordinates')
view_menu.addSeparator()
io_links = view_menu.addAction('Show IO &Links')
io_links.setCheckable(True)
show_2d_models = view_menu.addAction('Show &Models in 2D')
show_2d_models.setCheckable(True)
show_2d_models.setChecked(True)
ent_names = view_menu.addAction('Entity &Names')
ent_names.setCheckable(True)
ent_names.setChecked(True)
radius_culling = view_menu.addAction('Radius &Culling')
radius_culling.setShortcut('C')
radius_culling.setCheckable(True)
radius_culling.setChecked(True)
view_menu.addSeparator()
view_menu.addAction('&Hide').setShortcut('H')
view_menu.addAction('Hide Unselected').setShortcut('Ctrl+H')
view_menu.addAction('&Unhide').setShortcut('U')
view_menu.addSeparator()
view_menu.addAction('Selection to Visgroup')
view_menu.addSeparator()
view_menu.addAction('&OpenGL Settings')

tools_menu = menu.addMenu('&Tools')
tools_menu.addAction('&Group').setShortcut('Ctrl+G')
tools_menu.addAction('&Ungroup').setShortcut('Ctrl+U')
tools_menu.addSeparator()
tools_menu.addAction('&Tie to Entitiy').setShortcut('Ctrl+T')
tools_menu.addAction('&Move to World').setShortcut('Ctrl+Shift+W')
tools_menu.addSeparator()
tools_menu.addAction('&Apply Texture').setShortcut('Shift+A')
tools_menu.addAction('&Replace Textures')
tools_menu.addAction('Texture &Lock').setShortcut('Shift+L')
tools_menu.addSeparator()
tools_menu.addAction('&Sound Browser').setShortcut('Alt+S')
tools_menu.addSeparator()
tools_menu.addAction('Transform').setShortcut('Crtl+M')
tools_menu.addAction('Snap Selection to Grid').setShortcut('Crtl+B')
tools_menu.addAction('Snap Selection to Grid Individually').setShortcut('Crtl+Shift+B')
tools_menu.addSeparator()
tools_menu.addAction('Flip Horizontally').setShortcut('Ctrl+L')
tools_menu.addAction('Flip Vertically').setShortcut('Ctrl+I')
tools_menu.addSeparator()
tools_menu.addAction('&Create Prefab').setShortcut('Ctrl+R')

help_menu = menu.addMenu('&Help')
help_menu.addAction('Offline Help').setShortcut('F1')
help_menu.addSeparator()
help_menu.addAction('About QtPyHammer')
help_menu.addAction('About Qt')
help_menu.addAction('License')
help_menu.addSeparator()
help_menu.addAction('Valve Developer Community')
help_menu.addAction('TF2Maps.net')

file_act = QtWidgets.QAction()
menu.addAction(file_act) # ???

window.setMenuBar(menu)

key_tools = QtWidgets.QToolBar('Tools 1')
key_tools.setMovable(False)
button_1 = key_tools.addWidget(QtWidgets.QToolButton())
window.addToolBar(QtCore.Qt.TopToolBarArea, key_tools)

# toolbars

##window.showMaximized() # start with maximised window
window.show()

new_tab() # REMEMBER! SIGNAL & SLOTS DON'T REPORT ERRORS!

for i, t in enumerate(tabs):
    # contexts aren't sharing?
    tabs[i].widget().layout().itemAt(1).widget().sharedGLsetup()

app.exec_() # loop?





