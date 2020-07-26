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
        filenames = []
        filenames.append("customdev/dev_measuregeneric01green.vtf")
        filenames.append("customdev/dev_measurewall01green.vtf")
        materials = "../../test_materials"
        textures = [(f, vtf.vtf(f"{materials}/{f}")) for f in filenames]
        texture_previews = QtWidgets.QListWidget() # could also be QListView
        texture_previews.setViewMode(QtWidgets.QListWidget.IconMode)
        texture_previews.setIconSize(QtCore.QSize(128, 128))
        texture_previews.setResizeMode(QtWidgets.QListWidget.Adjust)
        for texture_name, texture_vtf in textures:
            width = texture_vtf.thumbnail_width
            height = texture_vtf.thumbnail_height
            image = QtGui.QImage(texture_vtf.thumbnail, width, height,
                                 QtGui.QImage.Format_RGB888)
            image = image.scaled(128, 128) # must upscale for QIcon manually
            icon = QtGui.QIcon(QtGui.QPixmap.fromImage(image))
            item = QtWidgets.QListWidgetItem(icon, texture_name)
            texture_previews.addItem(item)
        layout.addWidget(texture_previews)
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
