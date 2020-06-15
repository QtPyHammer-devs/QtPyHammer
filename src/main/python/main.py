import sys
# Third-party
from fbs_runtime.application_context.PyQt5 import ApplicationContext
from PyQt5 import QtCore, QtGui
# QtPyHammer
from ui.core import MainWindow


def except_hook(cls, exception, traceback): # nessecary for debugging SLOTS
    sys.__excepthook__(cls, exception, traceback)
sys.excepthook = except_hook


if __name__ == '__main__':
    # QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts)
    QtGui.QSurfaceFormat.setDefaultFormat(QtGui.QSurfaceFormat())
    appctxt = ApplicationContext()       # 1. Instantiate ApplicationContext
    # need QSettings to store: (cached_property)
    #  recent files
    #  OpenGL settings
    #  game configurations
    #  default filepaths (SteamDir [grab on install])
    #  keybinds
    #  ...
    # a handfull of .ini files should be straightforward enough
    ### LOAD BEFORE INITIALISING MainWindow! ###

    # read .fgd(s) for entity_data
    # prepare .vpks (grab directories)
    # mount & tag custom data (check the gameinfo.txt for paths, accept others)
    window = MainWindow(ctx=appctxt)
    window.showMaximized()
    window.new_tab(appctxt.get_resource("vmfs/test2.vmf"))
    # ^ test case
    appctxt.app.quit()
    exit_code = appctxt.app.exec_()      # 2. Invoke appctxt.app.exec_()
    sys.exit(exit_code)
