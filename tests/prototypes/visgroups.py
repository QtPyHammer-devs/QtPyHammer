import sys

from PyQt5 import QtWidgets

sys.path.insert(0, "../../QtPyHammer")
from ui import viewport
from utilities import render


app = QtWidgets.QApplication([])

viewport = viewport.Viewport3D()
viewport.setGeometry(128, 64, 512, 512)
viewport.show()

class visgroup_manager(QtWidgets.QListView):
    def __init__(self, parent=None):
        super(visgroup_manager, self).__init__(parent)
        # generate auto visgroups from viewport.render_manager
        # update functions as getters?
        # dynamic user visgroups?

        # edit dialog for selected user visgroup

    # def updateItem(index):
    #     visibile = ... viewport.render_manager.
    #     viewport.render_manager.hide.update(visible)

visgroup_widget = QtWidgets.QDialog()
layout = QtWidgets.QVBoxLayout()
layout.setContentsMargins(0, 0, 0, 0)
visgroup_widget.setLayout(layout)
visgroup_widget.layout().addWidget(QtWidgets.QTabWidget())
visgroup_widget.layout().itemAt(0).widget().addTab(visgroup_manager(), "Auto")
visgroup_widget.layout().itemAt(0).widget().addTab(visgroup_manager(), "User")
visgroup_widget.setGeometry(64 + 128 + 512, 64 + 128, 192, 256)
visgroup_widget.show()

app.exec_()
