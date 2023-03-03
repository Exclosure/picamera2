from typing import Type

import pytest

from scicamera import Camera, FakeCamera
from scicamera.testing import mature_after_frames_or_timeout


@pytest.mark.parametrize("CameraClass", [Camera, FakeCamera])
def test_timeout_helper(CameraClass: Type[Camera]):
    camera = CameraClass()
    try:
        mature_after_frames_or_timeout(camera, 2, 0.2)
    except TimeoutError:
        print("Timed out! (expected)")

    camera.start()
    mature_after_frames_or_timeout(camera)
