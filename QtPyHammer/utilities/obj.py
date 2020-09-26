from __future__ import annotations
import os
import re
from typing import Dict, List


class Obj:
    name: str
    vertices: List[List[float]]  # [(x, y, z)]
    normals: List[List[float]]  # [(x, y, z)]
    uvs: List[List[float]]  # [(u, v)]
    faces: List[List[List[int]]]  # [[(v_index, vn_index, vt_index), (...)], ...]
    objects: Dict[str, List[int]]  # {"object_name": (faces_start, faces_length)}
    groups: Dict[str, List[int]]  # {"group_name": (faces_start, faces_length)}

    def __init__(self, name, v=[], vn=[], vt=[], f=[], o={}, g={}):
        self.name = name
        self.vertices = v  # vertex positions
        self.normals = vn  # vertex normals
        self.uvs = vt  # vertex texture coordinates
        self.faces = f  # faces (v, vn, vt indices for each edge / polygon)
        self.objects = o  # objects (spans in faces)
        self.groups = g  # groups (spans [of objects] in faces)

        if None not in self.objects.keys():
            start = min([S for S, L in self.objects.values()])
            if start > 0:
                self.objects[None] = [0, start - 1]
        if None not in self.groups.keys():
            start = min([S for S, L in self.groups.values()])
            if start > 0:
                self.groups[None] = [0, start - 1]

        # self.objects_in_group = dict()
        # ^ {"group": ["object"]}
        # TODO: generate self.objects_in_group

    def __repr__(self) -> str:
        return f"<Obj with {len(self.f)} faces across {len(self.o)} models>"

    def raycast_intersects(self, ray_direction, ray_length):
        """Does the ray intersect any faces?"""
        raise NotImplementedError()

    @staticmethod
    def load_from_file(filename) -> Obj:  # noqa: C901
        """Creates a Obj object from the definition in filename"""
        vertex_data = {"v": [], "vt": [], "vn": []}
        faces = []
        current_object = None
        objects = {None: [0, 0]}
        current_group = None
        groups = {None: [0, 0]}
        # read file
        file = open(filename, "r")
        for line_number, line in enumerate(file.readlines()):
            if re.match(r"^[\t\ ]*$", line):
                continue
            try:
                line = line.split()
                line_type = line[0]
                line_data = line[1:]
                if line_type in ("v", "vn", "vt"):
                    vertex_data[line_type].append(list(map(float, line_data)))
                elif line_type == "f":
                    face = decode_face(line_data)
                    faces.append(face)
                    objects[current_object][1] += 1
                    groups[current_group][1] += 1
                elif line_type == "o":
                    current_object = " ".join(line_data)
                    objects[current_object] = [len(faces), 0]
                elif line_type == "g":
                    current_group = " ".join(line_data)
                    groups[current_group] = [len(faces), 0]
                # skipping all other line types
            except Exception as exc:
                print(f"Error on {line_number}:")
                raise exc
        file.close()
        # cleanup empty objects / groups
        if objects[None] == [0, 0]:
            objects.pop(None)
        if groups[None] == [0, 0]:
            groups.pop(None)
        name = os.path.basename(filename)
        return Obj(name, **vertex_data, f=faces, o=objects, g=groups)


def decode_face(index_strings: List[str]) -> List[List[int]]:
    face = []
    # ^ [(v_index, vn_index, vt_index)]
    for definition in reversed(index_strings):
        v_index, vn_index, vt_index = None, None, None
        definition.replace("\\", "/")
        if re.match(r"^[0-9]+$", definition):
            # f 1 2 3
            v_index = int(definition) - 1
        elif re.match(r"^[0-9]+/[0-9]+$", definition):
            # f 1/1 2/2 3/3
            v, vt = definition.split("/")
            v_index = int(v) - 1
            vt_index = int(vt) - 1
        elif re.match(r"^[0-9]+//[0-9]+$", definition):
            # f 1//1 2//2 3//3
            v, vn = definition.split("//")
            v_index = int(v) - 1
            vn_index = int(vn) - 1
        elif re.match(r"^[0-9]+/[0-9]+/[0-9]+$", definition):
            # f 1/1/1 2/2/2 3/3/3
            v, vt, vn = definition.split("/")
            v_index = int(v) - 1
            vt_index = int(vt) - 1
            vn_index = int(vn) - 1
        else:
            raise RuntimeError("Unexpected vertex definition")
        face.append((v_index, vn_index, vt_index))
    return face
