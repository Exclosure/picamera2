import time
from logging import getLogger
from typing import Type

import pytest

from scicamera import Camera, FakeCamera
from scicamera.testing import mature_after_frames_or_timeout

_log = getLogger(__name__)


@pytest.mark.parametrize("CameraClass", [Camera, FakeCamera])
def test_different_name_start_stop_runloop(CameraClass: Type[Camera]):
    with CameraClass() as camera:
        camera.start()
        mature_after_frames_or_timeout(camera)

        for _ in range(2):
            camera.stop_preview()
            camera.start_preview()

        mature_after_frames_or_timeout(camera)
        camera.stop()


@pytest.mark.parametrize("CameraClass", [Camera, FakeCamera])
def test_start_stop(CameraClass: Type[Camera]):
    import gc

    with CameraClass() as camera:
        for cycle in range(3):
            _log.warning("Starting camera %s", cycle)
            camera.start()
            mature_after_frames_or_timeout(camera)
            time.sleep(0.1)
            gc.collect()

            camera.stop()
            _log.warning("Stopped camera %s", cycle)
            camera.allocator = None
            time.sleep(0.1)
            gc.collect()
