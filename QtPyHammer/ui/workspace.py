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
    def __init__(self, vmf_path, new=True, parent=None):
        super(VmfTab, self).__init__(parent)
        self.filename = vmf_path
        self.never_saved = True if new else False
        self.selection_mode = selection_mode.group
        self.selection = set()
        # ^ ("type", major_id, minor_id) e.g. ("brush", brush.id, face.id)
        ## UI
        layout = QtWidgets.QVBoxLayout() # holds the viewport
        # ^ 2 QSplitter(s) will be used for quad viewports
        self.viewport = viewport.MapViewport3D(self)
        self.viewport.raycast.connect(self.raycast)
        # self.viewport.setViewMode.connect(...)
        self.viewport.setFocus() # not working as intended
        layout.addWidget(self.viewport)
        self.setLayout(layout)
        # self.timeline = ops.timeline.edit_history() # also handles multiplayer
        ### EDIT TIMELINE NOTES ###
        # what happens when a user brings "logs in" and pushes all their changes to the shared state?
        # since we're still saving as .vmf, history is saved as it's own file
        # ? branches and reading timelines efficiently (chronological sorting) ?
        # append mode file writing
        ### END EDIT TIMELINE NOTES ###
        # TODO: viewport splitter(s), toolbar (grid controls etc.),
        # selection mode widget, hotkeys (defined in settings)
        self.map_file = VmfInterface(self, self.filename)
        # ^ define the VmfInterface last so it can connect to everything

    def raycast(self, ray_origin, ray_direction):
        """Get the object hit by ray"""
        ray_length = self.viewport.render_manager.draw_distance
        ray_end = ray_origin + ray_direction * ray_length
        intersection = dict()
        # ^ distance: ("brush", brush.id, brush.face.id)
        # -- distance: (type, major_id, minor_id)
        # if distance is already in intersection:
        # -- z-fighting, special case!
        for brush in self.map_file.brushes:
            if ("brush", brush.id) in self.viewport.render_manager.hidden:
                # ^ not taking the displacement draw mode into account
                continue
            probable_intersections = dict()
            # ^ distance(t): face.id
            for face in brush.faces:
                normal, distance = face.plane
                alignment = vector.dot(normal, ray_direction)
                if alignment > 0: # skip backfaces
                    continue
                # similar method to utilities.solid.clip
                origin_distance = vector.dot(normal, ray_origin) - distance
                end_distance = vector.dot(normal, ray_end) - distance
                origin_is_behind = bool(origin_distance < 0.01)
                end_is_behind = bool(end_distance < 0.01)
                if not origin_is_behind and end_is_behind:
                    t = origin_distance / (origin_distance - end_distance)
                    probable_intersections[t] = face.id
            # check if any probable intersection actually touches the solid
            for t, face_id in probable_intersections.items():
                P = vector.lerp(ray_origin, ray_end, t)
                valid = True
                for face in brush.faces:
                    if face.id == face_id:
                        continue
                    normal, distance = face.plane
                    if (vector.dot(normal, P) - distance) > -0.01:
                        valid = False # P is floating outside the brush
                if valid:
                    intersection[t] = ("brush", brush.id, face_id)
        if len(intersection) == 0:
            return # no intersections, move on
        closest = min(intersection.keys())
        # if other distances are close, give a pop-up like blender alt+select
        selected = intersection[closest]
        # look at selection mode, do we want groups?, only the selected face?
        # - if CRTL is held, add to selection OR subtract if already in selection
        self.selection = {selected}

        self.viewport.render_manager.hide(selected[:2])

    def save_to_file(self):
        print(f"(not) Saving {self.filename}... ", end="")
        # store the camera's location
        # store what is and isn't hidden (visgroups included)
        self.map_file.save(self.filename)
        print("(not) Saved!")
        self.never_saved = False

    def close(self):
        # release used memory eg. self.viewport.render_manager buffers
        super(VmfTab, self).close()
