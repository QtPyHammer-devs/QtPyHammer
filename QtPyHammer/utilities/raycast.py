from typing import Dict, List

from . import vector


class Ray:
    origin: vector.vec3
    direction: vector.vec3
    length: float

    def __init__(self, origin, direction, length):
        self.origin = origin
        self.direction = direction
        self.length = length

    def plane_intersect(self, plane: List[vector.vec3, float]):
        normal, distance = plane
        alignment = vector.dot(normal, self.direction)
        if alignment > 0:  # skip backfaces
            return None  # no intersection
        # similar method to utilities.solid.clip
        origin_distance = vector.dot(normal, self.origin) - distance
        end_distance = vector.dot(normal, self.end) - distance
        origin_is_behind = bool(origin_distance < 0.01)
        end_is_behind = bool(end_distance < 0.01)
        if not origin_is_behind and end_is_behind:
            t = origin_distance / (origin_distance - end_distance)
            return t  # lerp(self.origin, self.end, t) for coordinates
            # t is great for sorting by intersect depth


def raycast_brushes(ray: Ray, brushes: List[...]) -> Dict[int, tuple]:
    intersections = dict()
    # ^ distance: ("brush", brush.id, brush.face.id)
    # -- distance: (type, major_id, minor_id) <Renderable.uuid>
    # if distance is already in intersection:
    # -- z-fighting, special case!
    for brush in brushes:  # filter to visible / selectable only
        probable_intersections = dict()  # just this brush
        # ^ {distance(t): face.id}
        for face in brush.faces:
            t = Ray.plane_intersect(face.plane)
            if t is not None:
                probable_intersections[t] = face.id

        # check if any probable intersection actually touches the solid
        for t, face_id in probable_intersections.items():
            P = vector.lerp(ray.origin, ray.end, t)
            valid = True
            for face in brush.faces:
                if face.id == face_id:
                    continue  # skip yourself, we're checking against all others
                normal, distance = face.plane
                if (vector.dot(normal, P) - distance) > -0.01:
                    valid = False  # P is floating outside the brush
            if valid:
                intersections[distance] = ("brush", brush.id, face_id)  # Renderable.uuid
    return intersections


def raycast(ray, map_file):
    """Get the object hit by ray"""
    intersections = dict()
    # ^ distance: ("brush", brush.id, brush.face.id)
    # -- distance: (type, major_id, minor_id)
    # if distance is already in intersection:
    # -- z-fighting, special case!
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
