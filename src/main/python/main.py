import sys
# Third-party
from fbs_runtime.application_context.PyQt5 import ApplicationContext
from PyQt5 import QtCore
# QtPyHammer
from ui.core import MainWindow


def except_hook(cls, exception, traceback): # nessecary for debugging SLOTS
    sys.__excepthook__(cls, exception, traceback)
sys.excepthook = except_hook


if __name__ == '__main__':
    appctxt = ApplicationContext()       # 1. Instantiate ApplicationContext
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts)

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
    
    window = MainWindow()
    window.setWindowTitle('QtPyHammer')
    window.setGeometry(1920, 1080, 640, 480)
    window.showMaximized()
    
    exit_code = appctxt.app.exec_()      # 2. Invoke appctxt.app.exec_()
    sys.exit(exit_code)
