from logging import getLogger
from pprint import pprint

import pytest

from scicamera.camera import CameraManager
from scicamera.info import CameraInfo

_log = getLogger(__name__)


def _close_all_warn() -> int:
    n_closed = CameraManager.singleton().close_all()
    if n_closed > 0:
        _log.error(f"Test left %s cameras open", n_closed)
    return n_closed


def _log_camera_info():
    _log.info("Camera info:")
    for info in CameraInfo.global_camera_info():
        pprint(info)


@pytest.fixture(autouse=True)
def run_around_tests():
    _close_all_warn()
    _log_camera_info()
    yield
    n_closed = _close_all_warn()
    if n_closed > 0:
        pytest.fail(f"Test left {n_closed} cameras open")
