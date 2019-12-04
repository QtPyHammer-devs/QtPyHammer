"""QtPyHammer MapTab that holds and manages an open .vmf"""
from enum import Enum
import sys
# Third-party
from PyQt5 import QtCore, QtGui, QtWidgets
# Local
from . import viewport # ui
sys.path.insert(0, "../") # sibling packages
import ops
# import ops.timeline
# from utilities import entity
from utilities import render, solid, vmf


class selection_mode(Enum):
    solo = 0
    brush_entitiy = 1
    group = 2
    face = 3


class Workspace(QtWidgets.QWidget):
    def __init__(self, vmf_path, parent=None):
        super(Workspace, self).__init__(parent)
        self.vmf = ops.vmf.interface(self, open(vmf_path))
        self.render_manager = render.manager(parent.ctx)
        # warn if memory low
        # 2nd progress bar
        for b in self.vmf.brushes: # len() / i -> progress
            self.vmf.render_manager.add_brush(b)
        # for e in self.entities: # len() / i -> progress
        #     self.render_manager.add_entity(e)
        self.viewport = viewport.Viewport3D(60) # grab all render updates from viewport.parent.render_manager
        # self.viewport.raycast.connect(self.raycast)
        self.setCentralWidget(self.viewport)
        self.viewport.setFocus()
        # Viewport splitter(s)
        # tab toolbar (grid controls)
        self.selection_mode = selection_mode.group
        self.selection = {"brushes": [], "faces": [], "entities": [], "object": []}
        # self.selection.object is non-vmf objects i.e. a reference model / image
        # use set() or remember active selected object?
        # self.timeline = ops.timeline.edit_history() # also handles multiplayer
        ### EDIT TIMELINE NOTES ###
        # what happens when a user brings "logs in" and pushes all their changes to the shared state?
        # if it's all still .vmf how will we serialise the commit history?
        # branches and reading timelines efficiently (chronological sorting)
        # append mode file writing
        ### END EDIT TIMELINE NOTES ###

    # connect QActions from /ops and /addons/ops to self.vmf & self.edit_timeline
    # def ...():
    #     ...

    def raycast(self, ray):
        """Get the object hit by ray"""
        ... # return object hit by ray (if any)
        # function calling raycast decides what is done to the hit object
        # pick, add to selection, remove from selection, paint, etc.

    def close(self): # intercept a parent method
        # teardown render manager
        ...
