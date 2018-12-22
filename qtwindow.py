import sys
from PyQt5.QtWidgets import *


def print_methods(obj, filter_lambda=lambda x: True, joiner='\n'):
    methods = [a for a in dir(obj) if hasattr(getattr(obj, a), '__call__')]
    print(joiner.join([m for m in methods if filter_lambda(m) == True]))


# menu action class
# context menu (set shortcut)

# keybinds menu

app = QApplication(sys.argv)
window = QMainWindow()
window.setWindowTitle('QtPyHammer')
window.setGeometry(640, 400, 640, 480)

menu = QMenuBar()
file_menu = menu.addMenu('&File')
file_menu.addAction('&New').setShortcut('Ctrl+N')
f_open = file_menu.addAction('&Open')
f_open.setShortcut('Ctrl+O')

file_browser = QFileDialog() #???

connect(f_open, file_browser.show())
##print(dir(f_open))
##print('=' * 80)
##f_open.connect.
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

##print(dir(file_menu))

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
map_menu.addMenu('&Grid Settings')
map_menu.addMenu('U&nits')
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

view_menu = menu.addMenu('&View')
view_menu.addAction('&OpenGL Settings')
view_menu.addSeparator()
quad_view = view_menu.addAction('&Quad View')
quad_view.setShortcut('Ctrl+Alt+Q')
quad_view.setCheckable(True)
quad_view.setChecked(True)
view_menu.addSeparator()
# Use in GL viewports only
##view_2d = view_menu.addMenu('2D')
##view_2d.addAction('&X/Y')
##view_2d.addAction('&Y/Z')
##view_2d.addAction('&Z/X')
##view_3d = view_menu.addMenu('3D')
##view_menu.addSeparator()
##view_menu.addAction('Center 2D Views on selection').setShortcut('Ctrl+E')
##view_menu.addAction('Center 3D Views on selection').setShortcut('Ctrl+Shift+E')
##view_menu.addAction('Go To &Coordinates')
##view_menu.addSeparator()
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
help_menu.addAction('About')
help_menu.addSeparator()
help_sites = help_menu.addMenu('Helpful Sites')
help_sites.addAction('Valve Developer Community')
help_sites.addAction('TF2Maps.net')
help_menu.addAction('Offline Help').setShortcut('F1')

file_act = QAction()
menu.addAction(file_act) # ???

# Tabs
##window.addDockWidget(1, QDockWidget())
##window.addDockWidget(2, QDockWidget())

window.setMenuBar(menu)

##window.showMaximized() # start with maximised window
window.show()

app.exec_() # loop?





