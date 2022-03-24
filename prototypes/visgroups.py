import sys

from PyQt5 import QtCore, QtWidgets

sys.path.append("../../")
from QtPyHammer.ui.workspace import VmfTab  # noqa E402
# from QtPyHammer.utilities import render  # noqa E402


def except_hook(cls, exception, traceback):  # for debugging Qt slots
    sys.__excepthook__(cls, exception, traceback)


sys.excepthook = except_hook

# run Qt app
app = QtWidgets.QApplication([])
app.folder = "../../"
app.preferences = QtCore.QSettings("../../configs/preferences.ini", QtCore.QSettings.IniFormat)

window = QtWidgets.QMainWindow()
window.setLayout(QtWidgets.QHBoxLayout())

workspace = VmfTab("../../Team Fortress 2/tf/mapsrc/test2.vmf")
workspace.setMinimumSize(512, 512)
window.setCentralWidget(workspace)


class visgroup_item(QtWidgets.QTreeWidgetItem):
    def __init__(self, name, parent=None):
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
    def checkState(self, state):
        """0 = unchecked, 1 = partial, 2 = checked"""
        if state != self.checkState:
            super(visgroup_item, self).setCheckState(0, state)

    def addChild(self, name):
        super(visgroup_item, self).addChild(visgroup_item(name, self))

    def addChildren(self, *names):
        children = [visgroup_item(n, self) for n in names]
        super(visgroup_item, self).addChildren(children)


class auto_visgroup_manager(QtWidgets.QTreeWidget):
    # VmfRenderModel / QTreeView 
    def __init__(self, parent=None): # workspace to link to
        super(auto_visgroup_manager, self).__init__(parent)
        self.setHeaderHidden(True)
        master = visgroup_item("All")
        master.addChild("World Geometry")
        world = master.child(0)
        world.addChildren("Displacements", "Skybox")
        master.addChild("Entities")
        entities = master.child(1)
        entities.addChildren("Point Entities", "Brush Entities", "Triggers")
        master.addChild("World Detail")
        detail = master.child(2)
        detail.addChildren("Props", "func_detail")
        
        self.addTopLevelItem(master)
        master.checkState = 2
        master.setExpanded(True)
        world.setExpanded(True)
        entities.setExpanded(True)
        detail.setExpanded(True)

        self.itemChanged.connect(self.handle_visibility)

    def handle_visibility(self, item, column): # ignore column
        global workspace
        render_manager = workspace.viewport.render_manager
        renderables = []
        visgroup = item.data(0, 0)
        if visgroup == "func_detail":
            for classname, ent_id, brush_id in workspace.vmf.brush_entities:
                if classname == "func_detail":
                    renderables.append(("brush", brush_id))
        if visgroup == "Triggers":
            for classname, ent_id, brush_id in workspace.vmf.brush_entities:
                if classname.startswith("trigger_"):
                    renderables.append(("brush", brush_id))
        elif visgroup == "Displacements":
            for brush in workspace.vmf.brushes:
                if not brush.is_displacement:
                    continue
                for side in brush.faces:
                    if hasattr(side, "displacement"):
                        disp_id = (brush.id, side.id)
                        renderables.append(("displacement", disp_id))
        elif visgroup == "Skybox":
            for brush in workspace.vmf.brushes:
                if any([f.material.startswith("TOOLS/TOOLSSKYBOX") for f in brush.faces]):
                    renderables.append(("brush", brush.id))
        # toggle visgroup
        for renderable in renderables:
            if item.checkState == 0:
                render_manager.hide(renderable)
            if item.checkState == 2:
                render_manager.show(renderable)

    # BONUS:
    # dynamic user collections / visgroups; filtered by region, material & classname
    # have an edit dialog for selected user visgroup

master_widget = QtWidgets.QDockWidget()
tab_manager = QtWidgets.QTabWidget()
tab_manager.addTab(auto_visgroup_manager(), "Auto")
tab_manager.addTab(QtWidgets.QWidget(), "User")
master_widget.layout().setContentsMargins(0, 0, 0, 0)
master_widget.layout().addWidget(tab_manager)
master_widget.setMinimumSize(192, 256)
window.addDockWidget(QtCore.Qt.RightDockWidgetArea, master_widget)

window.show()
app.exec_()
