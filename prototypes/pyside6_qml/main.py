import math
import os
import struct
import sys
from typing import List

from PySide6.QtCore import Property, QByteArray, QObject
from PySide6.QtGui import QGuiApplication, QVector3D
from PySide6.QtQuick3D import QQuick3DGeometry
from PySide6.QtQml import QmlElement, QQmlApplicationEngine
import vmf_tool


# TODO: define all these QmlElements in other python files
# QmlElement decorator globals
QML_IMPORT_NAME = "Vmf"
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


def fan_indices(start: int, length: int) -> List[int]:
    if length < 3:
        raise RuntimeError(f"Invalid face! Only {length} vertices!")
    out = [start, start + 1, start + 2]
    for i in range(length - 3):
        out.extend((start, out[-1], start + 3 + i))
    return out


@QmlElement
class BrushGeometry(QQuick3DGeometry):
    """should be created dynamically"""
    _brush: vmf_tool.solid.Brush

    def __init__(self, brush: vmf_tool.solid.Brush):
        super().__init__()
        self._brush = brush
        self.rebuildGeometry()

    # TODO: signals & slots for editting geo etc.

    def rebuildGeometry(self):
        i = 0
        indices = list()
        vertices = list()
        mins = [math.inf] * 3
        maxs = [-math.inf] * 3
        for face in self._brush.faces:
            indices.extend(fan_indices(i, len(face.polygon)))
            for vertex in face.polygon:
                mins = [min(a, b) for a, b in zip(mins, vertex)]
                maxs = [max(a, b) for a, b in zip(maxs, vertex)]
                vertices.extend((*vertex, *face.plane[0], face.uaxis.linear_pos(vertex), face.vaxis.linear_pos(vertex)))
            i += len(face.polygon)
        self.setBounds(QVector3D(*mins), QVector3D(*maxs))  # needed for raycast picking
        # vertex data
        vertex_bytes = QByteArray(struct.iter_pack("8f", vertices))
        self.setVertices(vertex_bytes)
        self.addAttribute(QQuick3DGeometry.Attribute.PositionSemantic, 0, QQuick3DGeometry.ComponentType.F32Type)
        self.addAttribute(QQuick3DGeometry.Attribute.NormalSemantic, 3 * 4, QQuick3DGeometry.ComponentType.F32Type)
        self.addAttribute(QQuick3DGeometry.Attribute.TexCoord0Semantic, 6 * 4, QQuick3DGeometry.ComponentType.F32Type)
        self.setStride(8 * 4)
        # index data
        index_bytes = QByteArray(struct.iter_pack("H", indices))
        self.addAttribute(QQuick3DGeometry.Attribute.IndexSemantic, 0, QQuick3DGeometry.ComponentType.U16Type)
        self.setIndices(index_bytes)


@QmlElement
class VmfInterface(QObject):
    _vmf: vmf_tool.Vmf
    _status: str
    filename: str

    def __init__(self, parent=None, filename: str = ""):
        super().__init__(parent)
        self.filename = filename
        self._vmf = vmf_tool.Vmf(filename)
        self._status = "Loaded"

    def brushCount(self):
        return len(self._vmf.brushes)

    def brushGeometryAt(self, index: int) -> BrushGeometry:
        brushes = list(self._vmf.brushes.values())
        # TODO: link created Geo to brush to pass changes back
        return BrushGeometry(brushes[index])

    def brushColourAt(self, index: int) -> str:
        brushes = list(self._vmf.brushes.values())
        return "#" + "".join([f"{int(255*x):02X}" for x in brushes[index].colour])

    @Property(str)
    def source(self) -> str:
        return self.filename

    @source.setter
    def source(self, filename: str):
        """assumes this .vmf is being loaded from filename, rather than setting save location"""
        if filename.startswith("file://"):
            filename = filename[len("file://"):]
        self.filename = filename
        try:
            print(f"Loading {filename}...")
            # NOTE: qml has to wait for the file do load, this isn't made asyncronous in any way
            self._vmf = vmf_tool.Vmf.from_file(filename)
            print(f"Loaded {filename}!")
        except Exception as exc:
            # TODO: log error / throw a UserWarning (FileNotFound etc.)
            print(exc)


# TODO: create QObject / QQuick3DGeometry subclasses to generate brushes & tie them to python objects for parsing
# TODO: QObject of keybinds from .ini(s)

if __name__ == "__main__":
    app = QGuiApplication(sys.argv)

    engine = QQmlApplicationEngine()
    local_dir = os.path.dirname(__file__)
    engine.load(os.path.join(local_dir, "main.qml"))
    if len(engine.rootObjects()) == 0:
        sys.exit(-1)

    sys.exit(app.exec())
