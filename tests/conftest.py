from scicamera.camera import CameraManager

import pytest
from logging import getLogger

_log = getLogger(__name__)


def _close_all_warn():
    n_closed = CameraManager.singleton().close_all()
    if n_closed > 0:
        _log.error(f"Test left %s cameras open", n_closed)


@pytest.fixture(autouse=True)
def run_around_tests():
    _close_all_warn()
    yield
    _close_all_warn()