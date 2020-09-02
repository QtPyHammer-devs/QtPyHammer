"""https://github.com/snake-biscuits/vmf_tool"""
from .parser import parse, text_from
from ..solid import solid


class vmf:
    def __init__(self, filename):
        # how would a loading bar measure progress here?
        self.filename = filename
        with open(self.filename, "r") as vmf_file:
            self._namespace = parse(vmf_file)
        ## Worldspawn
        self.skybox = self._namespace.world.skyname
        self.detail_material = self._namespace.world.detailmaterial
        self.detail_vbsp = self._namespace.world.detailvbsp
        # ^ TEST to see if modifying these updates the namespace
        # (can we modify self._namespace with an overridden dict.update()?)
        self._brushes = dict()
        # ^ id: brush
        if hasattr(self._namespace.world, "solid"):
            self._namespace.world.solids = [self._namespace.world.solid]
        if hasattr(self._namespace.world, "solids"):
            for brush in self._namespace.world.solids:
                self._brushes[int(brush.id)] = brush
        self.entities = dict()
        # ^ id: entity
        if hasattr(self._namespace.world, "entity"):
            entity = self._namespace.world.entity
            self.entities[int(entity.id)] = entity
        elif hasattr(self._namespace.world, "entities"):
            for entity in self._namespace.world.entities:
                self.entities[int(entity.id)] = entity
        self.brush_entities = dict()
        # ^ entity.id: {brush.id, brush.id, ...}
        for entity_id, entity in self.entities.items():
            if hasattr(entity, "solid"):
                if not isinstance(entity, str):
                    entity.solids = [entity.solid]
            if hasattr(entity, "solids"):
                self.brush_entities[entity.id] = set()
                for brush in entity.solids:
                    if not isinstance(entity, str):
                        brush_id = int(entity.solid.id)
                        self._brushes[brush_id] = entity.solid
                        self.brush_entities[entity_id].add(brush_id)
        self.import_errors = []
        self.brushes = dict()
        # ^ brush.id: brush
        for i, brush_id in enumerate(self._brushes):
            try:
                brush = solid(self._brushes[brush_id])
            except Exception as exc:
                self.import_errors.append("\n".join(
                    [f"Solid #{i} id: {brush_id} is invalid.",
                    "{exc.__class__.__name__}: {exc}"]))
            else:
                self.brushes[brush_id] = brush
        # groups
        # user visgroups (& handler methods)
        # worldspawn data

    def save_to_file(self, filename=None):
        # requires that the namespace be updated with every change
        # also requires undo / redo affects the namespace
        # tl;dr make the namespace up to date with user changes
        if filename == None:
            filename = self.filename
        with open(filename, "w") as file:
            file.write(text_from(self._namespace))
