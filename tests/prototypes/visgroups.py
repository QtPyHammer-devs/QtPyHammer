from PyQt5 import QtCore, QtWidgets

import sys
sys.path.append("../../")
from QtPyHammer.ui.workspace import VmfTab
from QtPyHammer.utilities import render


def except_hook(cls, exception, traceback): # for debugging Qt slots
    sys.__excepthook__(cls, exception, traceback)
sys.excepthook = except_hook

app = QtWidgets.QApplication([])

workspace = VmfTab("../../test_maps/test2.vmf")
workspace.setGeometry(128, 64, 512, 512)
workspace.show()


class visgroup_item(QtWidgets.QTreeWidgetItem):
    def __init__(self, name, parent=None):
        # want to represent each entry with a QCheckBox
        # each will also have a connection based on state
        super(visgroup_item, self).__init__(parent, [name], 1000)
        self.updating_children = False

    @property
    def children(self):
        return [self.child(i) for i in range(self.childCount())]

    def setData(self, column, role, value):
        super(visgroup_item, self).setData(column, role, value)
        if role == 10: # checkState
            if value != 1:
                self.updating_children = True
                for child in self.children:
                    child.checkState = value
                self.updating_children = False
            if self.parent() != None:
                if not self.parent().updating_children:
                    siblings = self.parent().children
                    sibling_state = {s.checkState for s in siblings}
                    if len(sibling_state) == 1:
                        self.parent().checkState = value
                    else:
                        self.parent().checkState = 1

    @property
    def checkState(self):
        return super(visgroup_item, self).checkState(0)

    @checkState.setter
    def checkState(self, state): # formerly setCheckState
        """0 = unchecked, 1 = partial, 2 = checked"""
        super(visgroup_item, self).setCheckState(0, state) # column, state

    def addChild(self, name):
        super(visgroup_item, self).addChild(visgroup_item(name, self))

    def addChildren(self, *names):
        children = [visgroup_item(n, self) for n in names]
        super(visgroup_item, self).addChildren(children)


class auto_visgroup_manager(QtWidgets.QTreeWidget): # QTreeView
    def __init__(self, parent=None): # workspace to link to
        super(auto_visgroup_manager, self).__init__(parent)
        self.setHeaderHidden(True)
        world = visgroup_item("World Geometry")
        world.addChild("Displacements")
        world.addChild("Skybox")
        world.addChild("Entities")
        entities = world.child(2)
        entities.addChildren("Point Entities", "Brush Entities", "Triggers")
        world.addChild("World Detail")
        detail = world.child(3)
        detail.addChildren("Props", "func_detail")
        
        self.addTopLevelItem(world)
        world.checkState = 2
        world.setExpanded(True)
        world.child(2).setExpanded(True)
        world.child(3).setExpanded(True)

        def handle_visibility(item, column): # ignore column
            global workspace
            renderable_ids = []
            visgroup = item.data(0, 0)
            if visgroup == "func_detail":
                for classname, ent_id, brush_id in workspace.vmf.brush_entities:
                    if classname == "func_detail":
                        renderable_ids.append(("brush", brush_id))
            elif visgroup == "Displacements":
                for brush in workspace.vmf.brushes:
                    if not brush.is_displacement:
                        continue
                    for side in brush.faces:
                        if hasattr(side, "displacement"):
                            disp_id = (brush.id, side.id)
                            renderable_ids.append(("displacement", disp_id))
            elif visgroup == "Skybox":
                for brush in workspace.vmf.brushes:
                    if any([f.material.startswith("TOOLS/TOOLSSKYBOX") for f in brush.faces]):
                        renderable_ids.append(("brush", brush.id))
            # hide / show
            render_manager = workspace.viewport.render_manager
            if item.checkState == 0:
                for renderable_id in renderable_ids:
                    render_manager.hide_renderable(renderable_id)
            if item.checkState == 2:
                for renderable_id in renderable_ids:
                    render_manager.show_renderable(renderable_id)

        self.itemChanged.connect(handle_visibility)

        # self._model = QtWidgets.QAbstractItemModel()
        # # ^ subclass which models a viewport's render_manager's visibles
        # # -- via the workspace tab's vmf object
        # self.setModel(self._model)

        # connect auto visgroups to viewport.render_manager
        # updates to the model affect the render_manager via functions that
        # -- apply the filters
        # TODO: track hidden by selection and hidden by visgroup separately
        # BONUS:
        # -- dynamic user collection / visgroups; filtered by region & material

        # have an edit dialog for selected user visgroup

visgroup_widget = QtWidgets.QDialog()
layout = QtWidgets.QVBoxLayout()
layout.setContentsMargins(0, 0, 0, 0)
visgroup_widget.setLayout(layout)
visgroup_widget.layout().addWidget(QtWidgets.QTabWidget())
tab_manager = visgroup_widget.layout().itemAt(0).widget()
tab_manager.addTab(auto_visgroup_manager(), "Auto")
tab_manager.addTab(QtWidgets.QWidget(), "User")
visgroup_widget.setGeometry(64 + 128 + 512, 64 + 128, 192, 256)
visgroup_widget.show()

app.exec_()
