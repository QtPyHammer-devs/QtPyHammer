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
        self.viewport = viewport.Viewport3D(60)
        self.render_manager = render.manager(self.viewport, parent.ctx) # know memory limits
        self.render_manager.add_brushes(*self.vmf.brushes) # len() / i -> progress
        # self.render_manager.add_entities(*self.vmf.entities) # also track loading progress
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.viewport)
        self.setLayout(layout)
        self.viewport.setFocus()
        # self.viewport.raycast.connect(self.raycast)
        # Viewport splitter(s)
        # toolbar (grid controls etc.)
        # selection mode widget / hotkeys
        self.selection_mode = selection_mode.group
        self.selection = {"brushes": set(), "faces": set(), "entities": set()}
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
