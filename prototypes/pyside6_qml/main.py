import os
import sys

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

# QML classes
import qml_vmf  # noqa F401


if __name__ == "__main__":
    _old_excepthook = sys.excepthook

    def except_hook(cls, exception, traceback):  # for debugging Qt slots
        """Print all errors, don't allow Qt to silence anything"""
        sys.__excepthook__(cls, exception, traceback)

    sys.excepthook = except_hook

    # run main.qml
    app = QGuiApplication(sys.argv)

    engine = QQmlApplicationEngine()
    local_dir = os.path.dirname(__file__)
    engine.load(os.path.join(local_dir, "main.qml"))
    # TODO: add QObject of keybinds from .ini(s) to engine
    if len(engine.rootObjects()) == 0:
        sys.exit(-1)

    sys.exit(app.exec())
