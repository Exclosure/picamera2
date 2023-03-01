from scicamera import Camera, CameraConfig
from typing import Type
import pytest
from scicamera import FakeCamera

import numpy as np

@pytest.mark.parametrize("CameraClass", [Camera, FakeCamera])
def test_capture_file_encodings(CameraClass: Type[Camera]):
    """Capture a np.array directly from the camera."""
    camera = CameraClass()
    preview_config = CameraConfig.for_preview(camera, main={"size": (800, 600)})
    camera.configure(preview_config)

    camera.start()
    camera.discard_frames(2)
    array = camera.capture_array().result()
    assert isinstance(array, np.ndarray)
    camera.stop()

    camera.close()
