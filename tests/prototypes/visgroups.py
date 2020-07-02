from PyQt5 import QtWidgets

import sys
sys.path.append("../../")
from QtPyHammer.ui.workspace import VmfTab


app = QtWidgets.QApplication([])

viewport = VmfTab("../../test_maps/test2.vmf")
viewport.setGeometry(128, 64, 512, 512)
viewport.show()

class visgroup_manager(QtWidgets.QTreeWidget):
    # QTreeView gives a collapsable view of a Model
    # want each entry to be a QCheckBox
    # model should do the indentation
    def __init__(self, parent=None):
        super(visgroup_manager, self).__init__(parent)
        # self._model = QtWidgets.QAbstractItemModel()
        # # ^ subclass which models a viewport's render_manager's visibles
        # # -- via the workspace tab's vmf object
        # self.setModel(self._model)
        # generate auto visgroups from viewport.render_manager
        # update functions as getters?
        # dynamic user visgroups?

        # have an edit dialog for selected user visgroup

        # QtWidgets.QCheckBox(label)

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
