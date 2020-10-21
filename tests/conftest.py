import pytest

from hammer import QtPyHammerApp


@pytest.fixture(scope="session")
def qapp():
    yield QtPyHammerApp([])
