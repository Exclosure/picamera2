from typing import Type

import pytest

from scicamera import Camera, FakeCamera
from scicamera.testing import mature_after_frames_or_timeout


@pytest.mark.parametrize("CameraClass", [Camera, FakeCamera])
def test_start_stop_runloop(CameraClass: Type[Camera]):
    camera = CameraClass()
    camera.start()

    mature_after_frames_or_timeout(camera)

    for _ in range(2):
        camera.stop_preview()
        camera.start_preview()

    mature_after_frames_or_timeout(camera)
    camera.stop()
    camera.close()


@pytest.mark.parametrize("CameraClass", [Camera, FakeCamera])
def test_start_stop(CameraClass: Type[Camera]):
    camera = CameraClass()
    for _ in range(3):
        camera.start()
        mature_after_frames_or_timeout(camera)
        camera.stop()
    camera.close()
