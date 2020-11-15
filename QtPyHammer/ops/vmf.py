"""Interface for editing .vmf files and updating the associated edit timeline"""
from vmf_tool import Vmf


class VmfInterface:
    """Connects vmf to renderer"""
    def __init__(self, parent, vmf_filename):
        self.parent = parent  # for conection to parent.viewport.render_manager
        self._vmf = Vmf(vmf_filename)  # vmf object we are wrapping (private)
        if len(self._vmf.import_errors) > 0:
            print(*self._vmf.import_errors, sep="\n")
        self.brushes = self._vmf.brushes.values()
        # ^ exposed directly for ui.workspace.VmfTab.raycast()
        self.parent.viewport.render_manager.add_brushes(*self.brushes)
        # track changes with CRDT for Undo & Redo
        # add entities

    def save(self, filename):
        self._vmf.save_to_file(filename)

    # brush operations
    def add_brushes(self, *brushes):
        # inform CRDT of the change
        self._vmf.brushes.update({b.id: b for b in brushes})
        self.parent.viewport.render_manager.add_brushes(*brushes)

    def delete_brushes(self, *indices):
        # inform CRDT of the change
        indices = sorted(indices)
        for i, index in enumerate(indices):
            self.brushes.pop(index - i)

    def modify_brush(self, index, modifier, *args, **kwargs):
        """Modify a brush with modifier"""
        # inform CRDT of the change
        modifier(self.brushes[index], *args, **kwargs)
