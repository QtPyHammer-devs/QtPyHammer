from PyQt5 import QtWidgets

__doc__ = """An attempt at Firefox style tabs in Qt"""

if __name__ == "__main__":
    import sys

    def except_hook(cls, exception, traceback):
        sys.__excepthook__(cls, exception, traceback)
    sys.excepthook = except_hook # Python Debug
    
    app = QtWidgets.QApplication(sys.argv)
    window = QtWidgets.QMainWindow()
    window.setGeometry(256, 256, 512, 512)
    tab_bar = QtWidgets.QTabWidget()
    tab_bar.setMovable(True)
    tab_bar.setTabsClosable(True)
    tab_bar.tabCloseRequested.connect(tab_bar.removeTab)
    dock_01 = QtWidgets.QDockWidget('QDockWidget')
    #setObjectName (for findChild)
    dock_01.topLevelChanged.connect(lambda *args: print('!', *args))
    ## def undock tab (remove self)
    # tab_bar.widget(0).parentWidget() # find child index
    # del self (parent.removeTab(index)
    # def dock tab (insert)
    # when floating state changes
    # tab_bar.widget(index)
    tab_bar.addTab(dock_01, 'Wrapper Tab')
    tab_bar.addTab(QtWidgets.QWidget(), 'Tab 01')
    tab_bar.addTab(QtWidgets.QWidget(), 'Tab 02')
    # need signals to add, remove & insert
    # when docks are moved
    window.setCentralWidget(tab_bar)
    window.show()

    sys.exit(app.exec_())
