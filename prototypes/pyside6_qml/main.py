import os
import sys

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

# QML classes
import qml_vmf  # noqa F401


if __name__ == "__main__":
    app = QGuiApplication(sys.argv)

    engine = QQmlApplicationEngine()
    local_dir = os.path.dirname(__file__)
    engine.load(os.path.join(local_dir, "main.qml"))
    # TODO: add QObject of keybinds from .ini(s) to engine
    if len(engine.rootObjects()) == 0:
        sys.exit(-1)

    sys.exit(app.exec())
