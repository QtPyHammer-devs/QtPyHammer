""".qph file handler"""
from __future__ import annotations

from collections import namedtuple
import io
import os
import shutil
import struct
from typing import Any, Dict, List

from . import brush
from . import common

from vmf_tool import Vmf


SectionHeader = namedtuple("SectionHeader", ["name", "offset", "length"])


class Qph:
    # NOTE: a C++ library for the format would be nice to have
    _headers = dict[str, SectionHeader]
    brushes: List[Any]  # TODO: list the actual brush class
    filename: str
    release: str  # a1 / b2 / rc3 / final
    revision: int
    version: int = 0  # format version
    lump_classes: Dict[str, object] = {"BRSH": brush.Lump,
                                       "DISP": displacement.Lump,
                                       "ENTS": entity.Lump,
                                       "MATS": material.Lump,
                                       "WRLD": world.Lump}

    def __init__(self, filename: str = "Untitled"):
        self.brushes = []
        self.filename = filename
        self.release = "a1"
        self.revision = 0  # times saved

    @staticmethod
    def load(filename: str) -> Qph:  # File > Open
        """Supports .qph v0 format"""
        if not os.path.exists(filename):
            raise FileNotFoundError(f"Could not file .qph file: '{filename}'")
        qph_file = open(filename, "rb")
        self = Qph(qph_file.name)
        assert qph_file.read(4) == b"QTPY"
        self.version, self.revision = common.read_struct("2I", qph_file)
        if self.version != 0:
            raise NotImplementedError(f"Cannot load .qph v{self.version}")
        self.release = qph_file.read(4).decode("ascii")
        # lump headers
        self._headers = dict()
        for _ in range(16):
            name, start, length = common.read_struct("4s2I", qph_file)
            name = name.decode("ascii")
            section_header = SectionHeader(name, start, length)
            self._section_headers[name] = section_header

        # TODO: dynamically read from file via property(section)[index]
        def data_of(section_name: str) -> Any:
            header = self._section_headers[section_name]
            qph_file.seek(header.start)
            data = qph_file.read(header.length)
            return data

        # TODO: let subclasses extend this mapping
        for lump_name, function in read.items():
            function(data_of(lump_name))
        qph_file.close()
        return self

    def load_brushes(self, byte_data: bytes):
        """Takes a stream of binary brushes (from a file, or network packets)"""
        section_data = io.BytesIO(byte_data)
        while True:
            # TODO: replace with a brush class
            brush_id, side_count = common.struct_read("2I", section_data)
            sides = [common.struct_read("6i32s9f2h", section_data) for _ in range(side_count)]
            colour = common.struct_read("3f")
            brush = list()
            for side in sides:
                A = side[0]
                brush.append((A, B, C))
            self.brushes.append(brush)

    def save(self, backup=True):  # File > Save
        if backup:
            shutil.copy(self.filename, f"{self.filename}x")
        out_file = open(self.filename)

        def write(d):
            out_file.write(d)
        # .qph header
        write(b"QTPY")

        def write_struct(f, d):
            write(struct.pack(f, d))

        version = 0
        self.revision += 1
        write_struct("2I", (version, self.revision))
        write_struct("4s", self.release.encode("ascii"))
        ...

    def as_vmf(self, filename: str):
        # NOTE: default filename should be "folder/filename_release.vmf"
        out_vmf = Vmf()
        ...
        out_vmf.brushes.extend(self.brushes)
        ...
        # save to file
        out_file = open(filename, "w")
        out_file.write(out_vmf.as_string())
        out_file.close()
