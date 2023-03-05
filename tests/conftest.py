from logging import getLogger

import pytest

from scicamera.camera import CameraManager

_log = getLogger(__name__)


def _close_all_warn() -> int:
    n_closed = CameraManager.singleton().close_all()
    if n_closed > 0:
        _log.error(f"Test left %s cameras open", n_closed)
    return n_closed


@pytest.fixture(autouse=True)
def run_around_tests():
    _close_all_warn()
    yield
    n_closed = _close_all_warn()
    if n_closed > 0:
        pytest.fail(f"Test left {n_closed} cameras open")
