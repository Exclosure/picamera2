import io
from typing import Type

import pytest

from scicamera import Camera, CameraConfig
from scicamera.fake import FakeCamera
from scicamera.testing import mature_after_frames_or_timeout


@pytest.mark.parametrize("CameraClass", [Camera, FakeCamera])
def test_capture_to_buffer(CameraClass: Type[Camera]):
    """Test the ability to capture to a buffer"""
    camera = CameraClass()
    camera.configure(CameraConfig.for_preview(camera))
    camera.start()

    for _ in range(2):
        mature_after_frames_or_timeout(camera)
        data = io.BytesIO()
        camera.capture_file(data, format="jpeg").result()
        assert data.getbuffer().nbytes > 0
        mature_after_frames_or_timeout(camera)

    camera.close()
