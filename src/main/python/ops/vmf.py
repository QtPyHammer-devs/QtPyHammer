"""Interface for editing .vmf files and updating the associated edit timeline"""
sys.path.insert(0, "../") # sibling packages
# import ops.timeline as timeline
# from utilities import entity
from utilities import solid


class interface:
    def __init__(self, parent, vmf_file):
        self.parent = parent # MapTab holding this interface
        # start progress bar
        vmf = utilities.vmf.load(vmf_file) # len(lines) / i -> progress
        self.raw = vmf
        self.skybox = vmf.world.skyname
        self.detail_material = vmf.world.detailmaterial
        self.detail_vbsp = vmf.world.detailvbsp
        self.brushes = []
        if hasattr(vmf.world, "solids"):
            self.brushes = vmf.world.solids
        elif hasattr(vmf.world, "solid"):
            self.brushes.append(vmf.world.solid)
        self.solids = [solid.import(b) for b in self.brushes] # len() / i -> progress
        # self.entities = []
        # if hasattr(vmf, "entities"):
        #     self.entities = vmf.world.entities
        # elif hasattr(vmf, "entitiy"):
        #     self.entities.append(vmf.world.entity)
        # self.entities = [entity.import(e) for e in self.entities] # len() / i -> progress

    def add_brush(self, brush):
        # self.parent.edit_timeline.add(timeline.op.BRUSH_ADD, brush, index)
        self.brushes.append(brush)
        # self.parent.render_manager

    def delete_brush(self, index):
        # self.parent.edit_timeline.add(timeline.op.BRUSH_DEL, brush, index)
        self.brushes.pop(index)

    def modify_brush(self, index, modifier, *args, **kwargs): # triggered by QActions
        # self.parent.edit_timeline.add(timeline.op.BRUSH_MOD, brush, index, mod, args, kwargs)
        modifier(self.brushes[index], *args, **kwargs)
