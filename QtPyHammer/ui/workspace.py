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
        # DEBUG
        print("+" * 20)
        def decode_colour(c):
            r, g, b = [int(255) * i for i in c]
            if (r, g, b) == (255, 0, 255):
                return "Center"
            out = ""
            out += "+X " if r == 255 else "-X "
            out += "+Y " if g == 255 else "-Y "
            out += "+Z " if b == 255 else "-Z "
            return out
        # ^ DEBUG
        intersection = dict()
        # ^ distance: ("brush", brush.id, brush.face.id)
        # -- distance: (type, major_id, minor_id)
        # if distance is already in intersection:
        # -- z-fighting, special case!
        for brush in self.vmf.brushes:
            # DEBUG
            print("=" * 20)
            brush_tag = decode_colour(brush.colour)
            print(f"brush_tag = {brush_tag}")
            # ^ DEBUG
            for face in brush.faces:
                normal, distance = face.plane
                # DEBUG
                n = lambda **kwargs: tuple(vector.vec3(**kwargs))
                nickname = {n(x=1): "+X", n(x=-1): "-X",
                            n(y=1): "+Y", n(y=-1): "-Y",
                            n(z=1): "+Z", n(z=-1): "-Z"}
                print(nickname[tuple(normal)], distance)
                # ^ DEBUG
                alignment = vector.dot(normal, ray_direction)
                print(f"{alignment = :0.5f}")
                if alignment > 0: # -1 == ray is opposite of normal
                    # ignoring backfaces
                    print(f"skipping {nickname[tuple(normal)]}")
                    print("-" * 15)
                    continue
                starts_behind = vector.dot(ray_origin, normal) > distance
                ends_behind = vector.dot(ray_end, normal) >= distance
                print(f"{starts_behind} {ends_behind}")
                if not starts_behind and not ends_behind:
                    break # the ray cannot intersect this brush
                elif starts_behind and not ends_behind:
                    ... # CLIP!
                    # this intersection's distance along ray
            # check each potential intersection touches the solid
            # (clipping test against other faces)
            # can we get away with just the planes aligned with the camera?
                # get intersection's distance along the ray
                # distance = ...
                # intersection[distance] = ("brush", brush.id, face.id)
                print("-" * 15)
        # closest = min(intersection.keys())
        # selected = intersection[closest]
        ## special cases for very close intersections (z-fighting)
        # self.selection["brushes"] = {brush.id}
        # - if CRTL is held, add / subtract if already selected

    def close(self):
        # release used memory eg. self.viewport.render_manager buffers
        super(VmfTab, self).close()
