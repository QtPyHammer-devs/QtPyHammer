"""Interface for editing .vmf files and updating the associated edit timeline"""
import sys
sys.path.insert(0, "../") # sibling packages
# import ops.timeline as timeline
# from utilities import entity
from utilities import solid
from utilities.vmf import namespace_from


class interface:
    def __init__(self, parent, vmf_file):
        self.parent = parent # to update the MapTab's render manager
        self.source_vmf = namespace_from(vmf_file) # len(lines) / i -> progress
        self.skybox = self.source_vmf.world.skyname
        self.detail_material = self.source_vmf.world.detailmaterial
        self.detail_vbsp = self.source_vmf.world.detailvbsp
        raw_brushes = []
        if hasattr(self.source_vmf.world, "solids"):
            raw_brushes = self.source_vmf.world.solids
        elif hasattr(self.source_vmf.world, "solid"):
            raw_brushes.append(self.source_vmf.world.solid)
        self.brushes = [] # len() / i -> progress
        for i, brush in enumerate(raw_brushes):
            try:
                valid_solid = solid.load(brush)
            except Exception as exc:
                report = "Solid #{} id: {} is invalid.\n{}".format(i, brush.id, exc)
                self.import_log.append(report)
            else:
                self.brushes.append(valid_solid)
        # self.entities = []
        # if hasattr(vmf, "entities"):
        #     self.entities = vmf.world.entities
        # elif hasattr(vmf, "entitiy"):
        #     self.entities.append(vmf.world.entity)
        # self.entities = [entity.import(e) for e in self.entities] # len() / i -> progress

    def add_brushes(self, *brushes):
        # self.parent.edit_timeline.add(timeline.op.BRUSH_ADD, brushes)
        for brush in brushes:
            self.brushes.append(brush)
        # self.parent.render_manager.add_brushes(*brushes)

    def delete_brushes(self, *indices):
        # self.parent.edit_timeline.add(timeline.op.BRUSH_DEL, brushes)
        indices = sorted(indices)
        for i, index in enumerate(indices):
            self.brushes.pop(index - i)

    def modify_brush(self, index, modifier, *args, **kwargs): # triggered by QActions
        # self.parent.edit_timeline.add(timeline.op.BRUSH_MOD, brush, index, mod, args, kwargs)
        modifier(self.brushes[index], *args, **kwargs)
