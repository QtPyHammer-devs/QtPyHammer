"""QtPyHammer Workspace that holds and manages an open .vmf file"""
from enum import Enum

from PyQt5 import QtCore, QtGui, QtWidgets

from . import viewport
from ..ops.vmf import VmfInterface
# from ..ops import timeline
# from ..utilities import entity
from ..utilities import render
from ..utilities import solid
from ..utilities import vector
from ..utilities import vmf


class selection_mode(Enum):
    solo = 0
    brush_entitiy = 1
    group = 2
    face = 3


class VmfTab(QtWidgets.QWidget):
    """Holds the .vmf data and viewport(s)"""
    def __init__(self, vmf_path, parent=None):
        super(VmfTab, self).__init__(parent)
        self.viewport = viewport.MapViewport3D(self)
        # self.viewport.setViewMode.connect(...)
        self.vmf = VmfInterface(self, open(vmf_path))
        layout = QtWidgets.QVBoxLayout() # holds the viewport
        # ^ QSplitter(s) will be used for quad viewports
        layout.addWidget(self.viewport)
        self.setLayout(layout)
        self.viewport.setFocus() # not working
        self.viewport.raycast.connect(self.raycast) # get 3D ray from viewport
        self.selection_mode = selection_mode.group
        self.selection = {"brushes": set(), "faces": set(), "entities": set()}
        # self.timeline = ops.timeline.edit_history() # also handles multiplayer
        ### EDIT TIMELINE NOTES ###
        # what happens when a user brings "logs in" and pushes all their changes to the shared state?
        # since we're still saving as .vmf, history is saved as it's own file
        # ? branches and reading timelines efficiently (chronological sorting) ?
        # append mode file writing
        ### END EDIT TIMELINE NOTES ###
        # TODO: viewport splitter(s), toolbar (grid controls etc.),
        # selection mode widget, hotkeys (defined in settings)

    def raycast(self, ray_origin, ray_direction):
        """Get the object hit by ray"""
        ray_length = self.viewport.render_manager.draw_distance
        ray_end = ray_origin + ray_direction * ray_length
        print("+" * 20)
        for brush in self.vmf.brushes:
            print("=" * 20)
            print(f"{brush.id = }")
            states = set()
            for face in brush.faces:
                normal, distance = face.plane
                starts_behind = vector.dot(ray_origin, normal) > distance
                ends_behind = vector.dot(ray_end, normal) >= distance
                # ^ are we interpretting negative distances wrong?
                v = lambda **kwargs: tuple(vector.vec3(**kwargs))
                nickname = {v(x=1): "X+", v(x=-1): "X-",
                            v(y=1): "Y+", v(y=-1): "Y-",
                            v(z=1): "Z+", v(z=-1): "Z-",}
                print(nickname[tuple(normal)], distance)
                print(f"{starts_behind} {ends_behind}")
                print("-" * 15)
                states.add(starts_behind + ends_behind)
                # state == 0: perpindicular in front
                # state == 1: passes through
                # state == 2: perpindicular behind
            if 0 not in states:
                print(f"Intersects! {brush.id = } {states}")
                # get intersection's depth along ray
        # self.selection["brushes"] = {brush.id}
        # - if CRTL is held, add / subtract if already selected

    def close(self):
        # release used memory eg. self.viewport.render_manager buffers
        super(VmfTab, self).close()
