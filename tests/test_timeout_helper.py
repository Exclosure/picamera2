from typing import Type

import pytest

from scicamera import Camera, FakeCamera
from scicamera.testing import mature_after_frames_or_timeout


@pytest.mark.parametrize("CameraClass", [Camera, FakeCamera])
def test_timeout_helper(CameraClass: Type[Camera]):
    with CameraClass() as camera:
        with pytest.raises(TimeoutError):
            mature_after_frames_or_timeout(camera, 1, 0.1)

        camera.start()
        mature_after_frames_or_timeout(camera)
        camera.stop()
