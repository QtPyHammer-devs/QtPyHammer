import os # for searching / cataloging folders
import sys
import vpk

from PyQt5 import QtCore, QtGui, QtWidgets

current_dir = os.path.dirname(os.path.realpath(__file__))
qtpy_dir = os.path.join(current_dir, "../../QtPyHammer")
sys.path.append(qtpy_dir)
from utilities import vtf


class texture_browser(QtWidgets.QDialog):
    # https://doc.qt.io/qt-5/qdialog.html
    def __init__(self):
        super(texture_browser, self).__init__(parent=None)
        # pick a layout for the core widget
        # top has a scrolling page of texture thumbnails
        # bottom has filters, searchbar, OK & Cancel buttons
        layout = QtWidgets.QVBoxLayout()
        scroll_area = QtWidgets.QScrollArea()
        page = QtWidgets.QWidget()
        page.setLayout(QtWidgets.QGridLayout())
        for y in range(22):
            for x in range(8):
                label = QtWidgets.QLabel()
                # Placeholder Image
                magenta = b"\xFF\x00\xFF"
                black = b"\x00\x00\x00"
                data = magenta + black + black + magenta

                # Parse data into image
                image = QtGui.QImage(data, 2, 2, QtGui.QImage.Format_RGB888)
                image.setDevicePixelRatio(1 / 32) # scale *32
                label.setPixmap(QtGui.QPixmap.fromImage(image))
                page.layout().addWidget(label, x, y)
        scroll_area.setWidget(page)
        scroll_area.setHorizontalScrollBarPolicy(1) # Always Off
        scroll_area.setVerticalScrollBarPolicy(2) # Always On
        layout.addWidget(scroll_area)
        layout.addWidget(QtWidgets.QLabel("Search Options")) # placeholder
        
        searchbar = QtWidgets.QLineEdit()
        layout.addWidget(searchbar)
        
        passSearchVar = lambda : self.search(searchbar.text())
        # searchbar.returnPressed.connect(passSearchVar) 
        searchButton = QtWidgets.QPushButton("Search")
        searchButton.clicked.connect(passSearchVar)
        searchButton.setDefault(1)
        layout.addWidget(searchButton)

        buttonbox = QtWidgets.QDialogButtonBox
        buttons = buttonbox(buttonbox.Ok | buttonbox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def search(self, keyword):
        print(f"Trying to Search {keyword}!")


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)
sys.excepthook = except_hook # For debugging python inside Qt Classes

app = QtWidgets.QApplication(sys.argv)
window = texture_browser()
window.setGeometry(128, 64, 576, 576)
window.show()

app.exec_()
