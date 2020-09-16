"""Interface for loading, saving & editing .qph files (like .vmf but binary)"""
from ..utilities.qph import qph


class QphInterface:
    def __init__(self, parent, filename):
        self.parent = parent
        self.qph = qph(filename)
        # collections (named! like blender); groups, visgroups
        # -- can import collections like prefabs
        # -- should make a qph port of the abs pack
        # --- generate thumbnails for prefabs
        # editor data:
        # self.selection
        # self.edit_history
        # - activity heatmap (like github pulse)

    def add_brushes(self, *brushes):
        # self.parent.edit_timeline.add()
        self.qph.add_brushes(*brushes)
        self.parent.viewport.render_manager.add_brushes(*brushes)
        raise NotImplementedError()
