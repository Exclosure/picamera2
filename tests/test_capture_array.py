from typing import Type

import numpy as np
import pytest

from scicamera import Camera, CameraConfig, FakeCamera
from scicamera.testing import mature_after_frames_or_timeout


@pytest.mark.parametrize("CameraClass", [Camera, FakeCamera])
def test_capture_file_encodings(CameraClass: Type[Camera]):
    """Capture a np.array directly from the camera."""
    camera = CameraClass()
    preview_config = CameraConfig.for_preview(camera, main={"size": (800, 600)})
    camera.configure(preview_config)

    camera.start()
    mature_after_frames_or_timeout(camera, 0.5)
    array = camera.capture_array().result()
    assert isinstance(array, np.ndarray)
    camera.stop()

    camera.close()
