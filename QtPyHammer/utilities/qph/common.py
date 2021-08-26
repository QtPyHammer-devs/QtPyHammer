from __future__ import annotations
import struct
from typing import Any, Dict, List


def struct_read(_format: str, file) -> List[Any]:
    return struct.unpack(_format, file.read(struct.calcsize(_format)))


def struct_write(_format: str, file, _tuple: List[Any]):
    return file.write(struct.pack(_format, *_tuple))


class BinaryStruct:
    __slots__: List[str]
    _arrays: Dict[str, int]
    # {"attr": length}
    # TODO: implement _children:  attr is instanced as class, list(self.attr) must match input
    _children: Dict[str, type] = dict()
    # {"attr": <class `child`>}
    _format: str

    def __init__(self, *args):
        # TODO: init all attrs to 0 / None / "", and accept kwargs
        # current case requires all args be defined
        # a strict __init__ with error cases would be best
        for attr, value in zip(self.__slots__, args):
            # cursed nesting approach
            # TODO: explicit is better than implicit;  use a dict to map types
            # NOTE: must be reversible via `list(self.attr)`
            SubStruct = self.__dict__.get("__annotations__", dict()).get(attr, None)
            if isinstance(SubStruct, BinaryStruct):
                value = SubStruct(*value)
            setattr(self, attr, value)

    def __iter__(self):
        """loop over the tuple struct.pack() needs to pack this object"""
        as_list = list()
        for attr in self.__slots__:
            value = getattr(self, attr)
            SubStruct = self.__dict__.get("__annotations__", dict()).get(attr, None)
            if SubStruct is not None:
                value = list(value)  # reCURSE *^*
            as_list.append(value)
        return iter()

    # should be a staticmethod, but can't be  ;\/__\/.
    # (1) staticmethods can't access class variables
    # (2) sublasses don't inherit staticmethods
    # (3) super() always breaks inside a staticmethod
    def from_file(self, file) -> BinaryStruct:
        # TODO: get class Child(BinaryStruct) sizes invisibly (SUPER HARD TO DO)
        # to go one step further: `struct Child { int count; OtherType values[count]; };`
        # and this is to go even further beyond: parse a C header of struct definitions
        data = struct_read(file, self._format)
        out_attrs = list()
        i = 0
        for attr in self.__slots__:
            if attr in self.__dict__.get("_arrays", dict()):
                count = self._arrays[attr]
                value = data[i:i + count]
                i += count
            else:
                value = data[i]
                i += count
            out_attrs.append(value)
        # TODO: handle overflow & underflow of args / __slots__
        return super(BinaryStruct, self).__init__(*out_attrs)

    def write(self, file):
        data = [getattr(self, a) for a in self.__slots__]
        struct_write(self._format, file, data)
