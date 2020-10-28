import os

import pytest

from hammer import QtPyHammerApp


os.environ.setdefault("PYTEST_QT_API", "pyqt5")
pytest_plugins = ["pytest-qt"]


@pytest.fixture(scope="session")
def qapp(qapp_args):
    yield QtPyHammerApp(qapp_args)
