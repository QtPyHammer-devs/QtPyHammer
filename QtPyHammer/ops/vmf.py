"""Interface for editing .vmf files and updating the associated edit timeline"""
import sys

sys.path.insert(0, "../") # sibling packages
# import ops.timeline as timeline
# from utilities import entity
from utilities import solid
from utilities.vmf import parse_lines


class interface:
    def __init__(self, parent, vmf_file):
        self.parent = parent # to update the MapTab's render manager
        self.log = []
        self.source_vmf = parse_lines(vmf_file.readlines())
        # the following should be editable from a QDialog
        self.skybox = self.source_vmf.world.skyname
        self.detail_material = self.source_vmf.world.detailmaterial
        self.detail_vbsp = self.source_vmf.world.detailvbsp
        # brush --> utilities.solid.solid
        source_brushes = []
        if hasattr(self.source_vmf.world, "solids"):
            source_brushes = self.source_vmf.world.solids
        elif hasattr(self.source_vmf.world, "solid"): # only one brush
            source_brushes.append(self.source_vmf.world.solid)
        qph_brushes = []
        for i, source_brush in enumerate(source_brushes):
            try:
                qph_brush = solid.solid(source_brush)
                qph_brushes.append(qph_brush)
            except Exception as exc:
                self.log.append(f"Solid #{i} id: {source_brush.id} is invalid.\n{exc}")
                raise exc
        self.brushes = []
        self.add_brushes(*qph_brushes)
        # self.add_entities(*entities)
        if len(self.log) > 0:
            print(*self.log, sep="\n")

    # the following methods need to be attached to QActions
    def add_brushes(self, *brushes):
        # self.parent.edit_timeline.add(timeline.op.BRUSH_ADD, brushes)
        self.brushes.extend(brushes)
        self.parent.viewport.render_manager.add_brushes(*brushes)

    def delete_brushes(self, *indices):
        # self.parent.edit_timeline.add(timeline.op.BRUSH_DEL, brushes)
        indices = sorted(indices)
        for i, index in enumerate(indices):
            self.brushes.pop(index - i)

    def modify_brush(self, index, modifier, *args, **kwargs):
        # self.parent.edit_timeline.add(timeline.op.BRUSH_MOD, brush, index, mod, args, kwargs)
        modifier(self.brushes[index], *args, **kwargs)
