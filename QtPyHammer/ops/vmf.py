from typing import Set, Tuple

from vmf_tool import Vmf


# TODO: Edit History (CRDT) for instance
# TODO: separate file data from render_manager updates


NodeId = Tuple[str, int, int]
# ^ ("type", major_id, minor_id)


class VmfInterface:
    """Connects vmf to renderer"""
    _vmf: Vmf
    # parent: ui.workspace.VmfTab  # connection to render_manager
    # -- parent.viewport.render_manager
    brushes: ...
    # ^ exposed directly for ui.workspace.VmfTab.raycast()
    hidden: ...
    # ^ bad implementation idea
    selection: Set[NodeId]
    # ^ set of ids?

    def __init__(self, parent, vmf_filepath: str):
        self.parent = parent
        self.selection = set()

        # TODO: edit timeline for instance (CRDT; Undo & Redo)
        # -- app.edit_history[instance_guid]?

        self._init_vmf(vmf_filepath)

        self.parent.viewport.render_manager.add_brushes(*self.brushes)
        # TODO: apply hide to render_manager
        # TODO: inform hide related UI if anything is hidden

    def _init_vmf(self, vmf_filepath: str):
        self._vmf = Vmf.from_file(vmf_filepath)
        # TODO: communicate loading time & errors to user
        self.brushes = self._vmf.brushes.values()
        # ^ exposed directly for ui.workspace.VmfTab.raycast()
        self.hidden = self._vmf.hidden

    def save(self, filepath: str):
        # TODO: use QtCore.QSaveFile
        self._vmf.save(filepath)

    # brush operations
    def add_brushes(self, *brushes):
        # TODO: inform CRDT of the change
        self._vmf.brushes.update({b.id: b for b in brushes})
        self.parent.viewport.render_manager.add_brushes(*brushes)

    def delete_brushes(self, *indices):
        # TODO: inform CRDT of the change
        indices = sorted(indices)
        for i, index in enumerate(indices):
            self.brushes.pop(index - i)

    def modify_brush(self, index, modifier, *args, **kwargs):
        """Modify a brush with modifier"""
        # TODO: inform CRDT of the change
        modifier(self.brushes[index], *args, **kwargs)
