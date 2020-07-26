import os # for searching / cataloging folders
import sys

from PyQt5 import QtCore, QtGui, QtWidgets

sys.path.insert(0, "../../QtPyHammer")
from utilities import vtf


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)
sys.excepthook = except_hook # Python Qt Debug

app = QtWidgets.QApplication(sys.argv)

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
        materials = "../../test_materials"
        filenames = []
        filenames.append(f"{materials}/customdev/dev_measuregeneric01green.vtf")
        filenames.append(f"{materials}/customdev/dev_measurewall01green.vtf")
        textures = {f: vtf.vtf(f) for f in filenames}
        for x, name in enumerate(textures):
            label = QtWidgets.QLabel()
            texture = textures[name]
            width = texture.thumbnail_width
            height = texture.thumbnail_height
            image = QtGui.QImage(texture.thumbnail, width, height,
                                 QtGui.QImage.Format_RGB888)
            label.setPixmap(QtGui.QPixmap.fromImage(image))
            label.setScaledContents(True)
            label.setMinimumSize(128, 128)
            page.layout().addWidget(label, 0, x)
        scroll_area.setWidget(page)
        scroll_area.setHorizontalScrollBarPolicy(1) # Always Off
        scroll_area.setVerticalScrollBarPolicy(2) # Always On
        layout.addWidget(scroll_area)
        layout.addWidget(QtWidgets.QLabel("Search Options")) # placeholder
        # ^ https://doc.qt.io/qt-5/qlabel.html
        # -- QLabels can hold text or images, great for markers
        buttonbox = QtWidgets.QDialogButtonBox
        buttons = buttonbox(buttonbox.Ok | buttonbox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setLayout(layout)

window = texture_browser()
# ^ make a subclass 
window.setGeometry(128, 64, 576, 576)
window.show()

app.exec_()
