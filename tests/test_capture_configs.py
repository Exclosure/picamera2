from typing import Type

import pytest

from scicamera import Camera, CameraConfig, FakeCamera
from scicamera.testing import mature_after_frames_or_timeout


@pytest.mark.parametrize(
    "config_method",
    [CameraConfig.for_preview, CameraConfig.for_video, CameraConfig.for_still],
)
@pytest.mark.parametrize("CameraClass", [Camera, FakeCamera])
def test_capture_config_video(CameraClass: Type[Camera], config_method):
    with CameraClass() as camera:
        config = config_method(camera)
        camera.configure(config)
        camera.start()
        mature_after_frames_or_timeout(camera)
        camera.stop()
