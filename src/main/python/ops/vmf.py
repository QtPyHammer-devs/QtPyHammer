"""Interface for editing .vmf files and updating the associated edit timeline"""
sys.path.insert(0, "../") # sibling packages
# import ops.timeline as timeline
# from utilities import entity
from utilities import solid
from utilities.vmf import namespace_from


class interface:
    def __init__(self, parent, vmf_file):
        self.parent = parent # MapTab holding this interface
        self.source_vmf = namespace_from(vmf_file) # len(lines) / i -> progress
        self.skybox = vmf.world.skyname
        self.detail_material = vmf.world.detailmaterial
        self.detail_vbsp = vmf.world.detailvbsp
        raw_brushes = []
        if hasattr(vmf.world, "solids"):
            raw_brushes = vmf.world.solids
        elif hasattr(vmf.world, "solid"):
            raw_brushes.append(vmf.world.solid)
        self.brushes = [] # len() / i -> progress
        for i, brush in enumerate(raw_brushes):
            try:
                valid_solid = solid.import(brush)
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

    def delete_brush(self, index):
        # self.parent.edit_timeline.add(timeline.op.BRUSH_DEL, brushes)
        self.brushes.pop(index)

    def modify_brush(self, index, modifier, *args, **kwargs): # triggered by QActions
        # self.parent.edit_timeline.add(timeline.op.BRUSH_MOD, brush, index, mod, args, kwargs)
        modifier(self.brushes[index], *args, **kwargs)
