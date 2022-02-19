import sys

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine


# TODO: create QObject / QQuick3DGeometry subclasses to generate brushes & tie them to python objects for parsing
# TODO: QObject of keybinds from .ini(s)

if __name__ == "__main__":
    app = QGuiApplication(sys.argv)

    engine = QQmlApplicationEngine()
    engine.load("main.qml")
    if len(engine.rootObjects()) == 0:
        sys.exit(-1)

    sys.exit(app.exec())
