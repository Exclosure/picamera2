from logging import getLogger

import pytest

from scicamera import Camera
from scicamera.camera import CameraManager

_log = getLogger(__name__)


@pytest.fixture
def camera() -> Camera:
    camera = Camera()
    yield camera

    if camera.is_open:
        camera.stop()
    camera.close()


def _close_all_warn():
    n_closed = CameraManager.singleton().close_all()
    if n_closed > 0:
        _log.error(f"Test left %s cameras open", n_closed)


@pytest.fixture(autouse=True)
def run_around_tests():
    _close_all_warn()
    yield
    _close_all_warn()
