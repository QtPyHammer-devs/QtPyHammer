"""Interface for editing .vmf files and updating the associated edit timeline"""
# from ..ops import timeline
# from ..utilities import entity
from ..utilities.solid import solid
from ..utilities.vmf import parse_lines, lines_from


class VmfInterface:
    def __init__(self, parent, vmf_file):
        self.parent = parent # to update the MapTab's render manager
        self.log = []
        self.source_vmf = parse_lines(vmf_file.readlines())
        # self.edit_timeline = timeline()
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
        source_entities = []
        if hasattr(self.source_vmf, "entity"):
            source_entities = [self.source_vmf.entity]
        elif hasattr(self.source_vmf, "entities"):
            source_entities.extend(self.source_vmf.entities)
        self.brush_entities = []
        for entity in source_entities:
            if hasattr(entity, "solid"): # brush entity
                if hasattr(entity.solid, "id"):
                    source_brushes.append(entity.solid)
                    tag = (entity.classname, int(entity.id), int(entity.solid.id))
                    self.brush_entities.append(tag)
            elif hasattr(entity, "solids"): # multi-brush entity
                if hasattr(entity.solids[0], "id"):
                    # ^ some entities may have both a "solid" flag & an embedded brush
                    # -- not checking this here, may be an issue later
                    source_brushes.extend(entity.solids)
                    for s in entity.solids:
                        tag = (entity.classname, int(entity.id), int(s.id))
                        self.brush_entities.append(tag)
        print(self.brush_entities)
        qph_brushes = []
        for i, source_brush in enumerate(source_brushes):
            try:
                qph_brush = solid(source_brush)
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
