from typing import Dict, List

from . import physics
from . import vector


class Ray:
    origin: vector.vec3
    direction: vector.vec3
    length: float

    def __init__(self, origin, direction, length):
        self.origin = origin
        self.direction = direction
        self.length = length

    def plane_intersect(self, plane: physics.Plane):
        alignment = vector.dot(plane.normal, self.direction)
        if alignment > 0:  # skip backfaces
            return None  # no intersection
        # similar method to utilities.solid.clip
        origin_distance = vector.dot(plane.normal, self.origin) - plane.distance
        end_distance = vector.dot(plane.normal, self.end) - plane.distance
        origin_is_behind = bool(origin_distance < 0.01)
        end_is_behind = bool(end_distance < 0.01)
        if not origin_is_behind and end_is_behind:
            t = origin_distance / (origin_distance - end_distance)
            return t  # lerp(self.origin, self.end, t) for coordinates
            # t is great for sorting by intersect depth


def raycast_brushes(ray: Ray, brushes: List[object]) -> Dict[int, tuple]:
    intersections = dict()
    # ^ distance: ("brush", brush.id, brush.face.id)
    # -- distance: (type, major_id, minor_id) <Renderable.uuid>
    # if distance is already in intersection:
    # -- z-fighting, special case! (need a margin of error)
    for brush in brushes:

        probable_intersections = dict()  # just this brush
        # ^ {distance(t): face.id}
        for face in brush.faces:
            plane = physics.Plane(*face.plane)
            t = Ray.plane_intersect(plane)
            if t is not None:
                probable_intersections[t] = face.id

        # check if any probable intersection actually touches the solid
        for t, face_id in probable_intersections.items():
            P = vector.lerp(ray.origin, ray.end, t)
            valid = True
            for face in brush.faces:
                if face.id == face_id:
                    continue  # skip yourself, we're checking against all others
                other_plane = physics.Plane(*face.plane)
                if (vector.dot(other_plane.normal, P) - other_plane.distance) > -0.01:
                    valid = False  # P is floating outside the brush
                    break
            if valid:
                brush_t = min(probable_intersections.keys())
                intersections[brush_t] = ("brush", brush.id, face_id)  # Renderable.uuid
    return intersections


def raycast(ray: Ray, map_file):
    """Get the object hit by ray"""
    intersections = dict()
    # ^ distance: ("brush", brush.id, brush.face.id)
    # -- distance: (type, major_id, minor_id)
    # if distance is already in intersection:
    # -- z-fighting, special case!
    # TODO: only check against visible / selectable brushes
    selectable_brushes = [b for b in map_file.brushes if b.id not in map_file.hidden["brushes"]]
    intersections.update(raycast_brushes(ray, selectable_brushes))

    if len(intersections) == 0:
        return None  # no intersections, move on

    closest = min(intersections.keys())  # smallest t
    # TODO: if other distances are close, give a pop-up list; like Blender alt+select
    selected = intersections[closest]
    # TODO: selection mode
    # -- do we want this object's group?, only the selected face?
    # TODO: modifier keys, add to selection? subtract? new selection?

    return selected  # let the caller deal with selection mode
