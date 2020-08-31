"""Interface for loading, saving & editing .qph files (like .vmf but binary)"""
from ..utilities.qph import qph


class QphInterface:
    def __init__(self, file=None):
        if file == None: # File > New
            self.qph = qph("untitled")
            self.never_saved = True
        else: # File > Open
            self.qph = qph(filename)
            self.never_saved = False
        # collections (named! like blender); groups, visgroups
        # -- can import collections like prefabs
        # -- should make a qph port of the abs pack
        # --- generate thumbnails for prefabs
        ## editor data
        # self.selection
        # self.edit_history
        # - activity heatmap (like github pulse)

    def add_brushes(self, brushes):
        raise NotImplementedError()
        
