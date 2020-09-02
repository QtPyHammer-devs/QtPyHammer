"""Interface for editing .vmf files and updating the associated edit timeline"""
# from ..ops import timeline
# from ..utilities import entity
from ..utilities.solid import solid
from ..utilities.vmf import vmf


class VmfInterface:
    def __init__(self, parent, vmf_filename):
        self.parent = parent # conection to parent.viewport.render_manager
        self._vmf = vmf(vmf_filename)
        if len(self._vmf.import_errors) > 0:
            print(*self._vmf.import_errors, sep="\n")
        self.brushes = self._vmf.brushes.values()
        # ^ needed for ui.workspace.VmfTab.raycast()
        self.parent.viewport.render_manager.add_brushes(*self.brushes)
        # self.edit_timeline = timeline()
        # self.add_entities(*entities)

    def add_brushes(self, *brushes):
        # self.parent.edit_timeline.add(timeline.op.BRUSH_ADD, brushes)
        self._vmf.brushes.update({b.id: b for b in brushes})
        self.parent.viewport.render_manager.add_brushes(*brushes)

    def delete_brushes(self, *indices):
        # self.parent.edit_timeline.add(timeline.op.BRUSH_DEL, brushes)
        indices = sorted(indices)
        for i, index in enumerate(indices):
            self.brushes.pop(index - i)

    def modify_brush(self, index, modifier, *args, **kwargs):
        # self.parent.edit_timeline.add(timeline.op.BRUSH_MOD, brush, index, mod, args, kwargs)
        modifier(self.brushes[index], *args, **kwargs)
