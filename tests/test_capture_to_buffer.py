import io

from typing import Type
from scicamera import Camera, CameraConfig
from scicamera.fake import FakeCamera

import pytest

@pytest.mark.parametrize("CameraClass", [Camera, FakeCamera])
def test_capture_to_buffer(CameraClass: Type[Camera]):
    """Test the ability to capture to a buffer"""
    camera = CameraClass()
    camera.configure(CameraConfig.for_preview(camera))
    camera.start()

    for _ in range(2):
        camera.discard_frames(2).result()
        data = io.BytesIO()
        camera.capture_file(data, format="jpeg").result()
        assert data.getbuffer().nbytes > 0
        camera.discard_frames(2).result()

    camera.close()
