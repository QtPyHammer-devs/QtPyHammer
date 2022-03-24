from __future__ import annotations

import math
import struct
from typing import List

from PySide6.QtCore import Property, QByteArray, QObject, Signal, Slot
from PySide6.QtGui import QVector3D
from PySide6.QtQuick3D import QQuick3DGeometry
from PySide6.QtQml import QmlElement
import vmf_tool


# QmlElement decorator globals
QML_IMPORT_NAME = "Vmf"
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


def fan_indices(start: int, length: int) -> List[int]:
    """converts line loop indices to triangle fan"""
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

    # TODO: signals & slots for editing geo etc.

    def rebuildGeometry(self):
        self.clear()
        i = 0
        indices = list()
        vertices = list()
        mins = [math.inf] * 3
        maxs = [-math.inf] * 3
        for face in self._brush.faces:
            if len(face.polygon) == 0:
                # some brushes are coming out with empty faces, should probably debug this in vmf_tool
                continue
            print(face.polygon)
            for vertex in face.polygon:
                mins = [min(a, b) for a, b in zip(mins, vertex)]
                maxs = [max(a, b) for a, b in zip(maxs, vertex)]
                vertices.append((*vertex, *face.plane[0], face.uaxis.linear_pos(vertex), face.vaxis.linear_pos(vertex)))
            indices.extend(fan_indices(i, len(face.polygon)))
            i += len(face.polygon)
        self.setBounds(QVector3D(*mins), QVector3D(*maxs))  # needed for raycast picking
        # vertex data
        vertex_bytes = QByteArray(b"".join([struct.pack("8f", *v) for v in vertices]))
        self.setVertexData(vertex_bytes)
        self.addAttribute(QQuick3DGeometry.Attribute.PositionSemantic, 0, QQuick3DGeometry.Attribute.F32Type)
        self.addAttribute(QQuick3DGeometry.Attribute.NormalSemantic, 3 * 4, QQuick3DGeometry.Attribute.F32Type)
        self.addAttribute(QQuick3DGeometry.Attribute.TexCoord0Semantic, 6 * 4, QQuick3DGeometry.Attribute.F32Type)
        self.setStride(8 * 4)
        # index data
        index_bytes = QByteArray(b"".join([struct.pack("H", i) for i in indices]))
        self.addAttribute(QQuick3DGeometry.Attribute.IndexSemantic, 0, QQuick3DGeometry.Attribute.U16Type)
        self.setIndexData(index_bytes)


@QmlElement
class VmfInterface(QObject):
    _vmf: vmf_tool.Vmf
    _status: str  # status Property (QEnum would be better but makes a lot of errors atm)
    filename: str  # source Property
    sourceChanged = Signal(str)
    statusChanged = Signal(str)

    def __init__(self, parent=None, filename: str = ""):
        super().__init__(parent)
        self.filename = filename  # source Property
        self._vmf = vmf_tool.Vmf(filename)
        self._status = "Unloaded"
        # TODO: Editted & Saved statuses for handling changes (e.g. unsaved changes / no changes)
        # internal Signal & Slot connections
        self.sourceChanged.connect(self.loadVmf)
        # ^ setting self.source reads the .vmf file at that location

    @Property(int)
    def brushCount(self):
        return len(self._vmf.brushes)

    @Slot(int, result=BrushGeometry)
    def brushGeometryAt(self, index: int) -> BrushGeometry:
        brushes = list(self._vmf.brushes.values())
        try:
            out = BrushGeometry(brushes[index])
            # TODO: link qml object to self._vmf.brushes to connect interface & object state (saving changes etc.)
        except Exception as exc:
            print(f"Brush {index} raised: {exc}")
            out = None
        return out

    @Slot(int, result=str)
    def brushColourAt(self, index: int) -> str:
        brushes = list(self._vmf.brushes.values())
        return "#" + "".join([f"{int(255*x):02X}" for x in brushes[index].colour])

    @Slot(str)
    def loadVmf(self, filename: str):
        # TODO: let a QRunnable & QThreadPool handle this on a seperate thread from the GUI
        try:
            self.status = "Loading"
            self._vmf = vmf_tool.Vmf.from_file(filename)
            self.status = "Loaded"
        except Exception as exc:
            print(f"While loading .vmf encountered: {exc}")
            # TODO: store some text detailing the error as a property
            self.status = "Error"

    @Property(str)
    def source(self) -> str:
        return self.filename

    @source.setter
    def source(self, new_filename: str):
        # TODO: test all target platforms & environments for irregular filenames
        # -- e.g. os.path.expandhome("~/filename.vmf") (users may enter path as text, if the FileDialog allows)
        if new_filename.startswith("file:///"):
            new_filename = new_filename[len("file:///"):]
        print(new_filename)
        if new_filename == self.filename:
            return
        self.filename = new_filename
        self.sourceChanged.emit(new_filename)

    @Property(str)
    def status(self) -> str:
        return self._status

    @status.setter
    def status(self, new_status: str):
        if new_status == self._status:
            return
        self._status = new_status
        self.statusChanged.emit(new_status)
