import io
import struct
from typing import List

from QtPyHammer.utilities.qph import BinaryStruct


data = (0, 1, 2, 0xFF, "ABCD")  # contents of test class


class BS_SubClass(BinaryStruct):
    __slots__ = ["origin", "flags", "name"]
    _format = "3fi4s"
    _arrays = {"origin": 3}

    origin: List[float]
    flags: int
    name: str


class TestBinaryStruct:
    def test_init(self):
        subclass = BS_SubClass((0, 1, 2), 0xFF, "ABCD")
        assert isinstance(subclass.name)

    def test_from_file(self):
        byte_data = struct.pack(BS_SubClass._format, *data)
        file = io.BytesIO(byte_data)
        subclass = BS_SubClass.from_file(file)
        file.seek(0)
        assert file.read() == struct.pack(*list(subclass))

    def test_write(self):
        file = io.BufferedReader(b"")
        subclass = BS_SubClass(*data)
        subclass.write(file)
        file.seek(0)
        assert file.read() == struct.pack(*list(subclass))


# TODO: test Qph class
