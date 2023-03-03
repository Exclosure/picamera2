from typing import Type

import pytest
from PIL import Image

from scicamera import Camera, CameraConfig
from scicamera.fake import FakeCamera
from scicamera.testing import mature_after_frames_or_timeout


@pytest.mark.parametrize("CameraClass", [Camera, FakeCamera])
def test_capture_image(CameraClass: Type[Camera]):
    """Capture a full resolution image to memory rather than to a file."""
    camera = CameraClass()
    camera.start_preview()
    preview_config = CameraConfig.for_preview(camera)
    capture_config = CameraConfig.for_still(camera)

    camera.configure(preview_config)
    camera.start()
    mature_after_frames_or_timeout(camera)

    image = camera.capture_image(config=capture_config).result()
    assert isinstance(image, Image.Image)

    mature_after_frames_or_timeout(camera)

    camera.close()
