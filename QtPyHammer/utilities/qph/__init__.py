""".qph file handler"""
from collections import namedtuple
import io
import shutil
import struct

# from vmf_tool import Vmf


class qph:
    def __init__(self, filename):
        self.filename = filename
        self.version = 0  # filetype version
        self.revision = 0  # times saved
        self.release = "a1"
        self.brushes = []

    @staticmethod
    def load(filename):  # File > Open
        """Supports .qph v0 format"""
        qph_file = open(filename, "rb")
        self = qph(qph_file.name)

        def read(x):
            return qph_file.read(x)

        def read_struct(f):
            return struct.unpack(f, read(struct.calcsize(f)))

        assert read(4) == b"QTPY"
        self.version, self.revision = read_struct("2I")
        if self.version != 0:
            raise NotImplementedError(f"Cannot load .qph v{self.version}")
        self.release = read(4).decode("ascii")
        self._headers = dict()
        header = namedtuple("header", ["name", "start", "length", "special"])
        for i in range(16):
            name, start, length, special = read_struct("4s3I")
            name = name.decode("ascii")
            lump_header = header(name, start, length, special)
            self._headers[name] = lump_header

        def data_of(lump_name):
            header = self._headers[lump_name]
            qph_file.seek(header.start)
            data = qph_file.read(header.length)
            return data
        read = {"BRSH": self.load_brushes,
                "DISP": self.load_displacements,
                "ENTS": self.load_entities,
                "WRLD": self.load_worldspawn}
        for lump_name, function in read.items():
            function(data_of(lump_name))
        qph_file.close()
        return self

    def load_brushes(self, byte_data):
        """Takes a stream of binary brushes (from a file, or network packets)"""
        data = io.BytesIO(byte_data)

        def read(*args):
            return data.read(*args)

        def read_struct(f):
            return struct.unpack(f, read(struct.calcsize(f)))

        def read_structs(c, f):
            return struct.unpack(f, read(struct.calcsize(f) * c))

        while True:
            brush_id, side_count = read_struct("2I")
            # sides = read_structs(side_count, "6i32s9f2I")
            # ^ use bsp_tool.mods.common.Base subclasses
            # int[3] plane.origin.xyz
            # int[3] plane.ratio.xyz
            # char[32] material
            # float[4] uaxis.xyzw
            # float[4] vaxis.xyzw
            # float rotation
            # uint lightmapscale
            # uint smoothing_groups
            # colour = read_struct("3f")
            # plane.origin & plane.ratio
            # - A = plane.origin + plane.ratio.x
            # - B = plane.origin + plane.ratio.y
            # - C = plane.origin + plane.ratio.z
            # - this way planes are always represented relative to the grid
            # - X+ plane is stored as the ratio 0:1:1
            # - X- as 0:-1:-1
            # ^ this'll be fun
            # brush = ...
            # self.brushes.append(brush)

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

    # def as_vmf(self):
    #     out_vmf = Vmf()
    #     ...
    #     out_vmf.brushes.extend(self.brushes)
    #     ...
    #     base_filename = os.path.splitext(self.filename)
    #     filename = os.path.join(folder, f"{base_filename}_{self.release}.vmf")
    #     out_file = open(filename, "w")
    #     out_file.write("".join(lines_from(out_vmf)))
    #     out_file.close()
