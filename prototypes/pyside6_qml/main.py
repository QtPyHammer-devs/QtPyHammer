import os
import sys

from PySide6 import QtCore
from PySide6 import QtGui
from PySide6 import QtQml
import vmf_tool


# TODO: load qml objects from separate files
# QmlElement decorator globals
QML_IMPORT_NAME = "Vmf"
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QtQml.QmlElement
class VmfInterface(QtCore.QObject):
    _vmf: vmf_tool.Vmf
    # TODO: a list of QML Models built from Brush objects to render in the View3D Scene

    fileLoaded = QtCore.Signal()

    @QtCore.Slot(str, result=bool)
    def loadFile(self, filename: str) -> bool:
        # TODO: proper error handling
        # NOTE: this is slow and should really update a progress bar somehow
        try:
            print(f"Loading {filename}...")
            self._vmf = vmf_tool.Vmf.from_file(filename)
            # TODO: create child QML objects for View3D etc.
            self.fileLoaded.emit()
        except Exception:
            # TODO: log error / throw a UserWarning (FileNotFound etc.)
            return False
        return True


# TODO: create QObject / QQuick3DGeometry subclasses to generate brushes & tie them to python objects for parsing
# TODO: QObject of keybinds from .ini(s)

if __name__ == "__main__":
    app = QtGui.QGuiApplication(sys.argv)

    engine = QtQml.QQmlApplicationEngine()
    local_dir = os.path.dirname(__file__)
    engine.load(os.path.join(local_dir, "main.qml"))
    if len(engine.rootObjects()) == 0:
        sys.exit(-1)

    sys.exit(app.exec())
