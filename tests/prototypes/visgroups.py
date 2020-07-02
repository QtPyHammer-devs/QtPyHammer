from PyQt5 import QtWidgets

import sys
sys.path.append("../../")
from QtPyHammer.ui.workspace import VmfTab
from QtPyHammer.utilities import render


app = QtWidgets.QApplication([])

workspace = VmfTab("../../test_maps/test2.vmf")
workspace.setGeometry(128, 64, 512, 512)
workspace.show()

def hide_brush(render_manager, brush_id):
    span = render_manager.buffer_location[("brush", brush_id)]["index"]
    span_list = render_manager.draw_calls["brush"]
    render_manager.draw_calls["brush"] = render.remove_span(span_list, span)
    render_manager.hidden["brush"].add(brush_id)

def show_brush(render_manager, brush_id):
    span = render_manager.buffer_location[("brush", brush_id)]["index"]
    span_list = render_manager.draw_calls["brush"]
    render_manager.draw_calls["brush"] = render.add_span(span_list, span)
    render_manager.hidden["brush"].discard(brush_id)

hide_brush(workspace.viewport.render_manager, 2)


class visgroup_item(QtWidgets.QTreeWidgetItem):
    def __init__(self, name):
        # want to represent each entry with a QCheckBox
        # each will also have a connection based on state
        super(visgroup_item, self).__init__([name], 0)

    def addChild(self, name):
        super(visgroup_item, self).addChild(visgroup_item(name))

    def addChildren(self, *names):
        children = [visgroup_item(n) for n in names]
        super(visgroup_item, self).addChildren(children)
        

class auto_visgroup_manager(QtWidgets.QTreeWidget): # QTreeView
    def __init__(self, parent=None): # workspace to link to
        super(auto_visgroup_manager, self).__init__(parent)
        self.setHeaderHidden(True)
        # AUTO VISGROUPS TREE
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
        world.setExpanded(True)
        world.child(2).setExpanded(True)
        world.child(3).setExpanded(True)

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
