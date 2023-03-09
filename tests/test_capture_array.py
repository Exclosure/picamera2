from typing import Type

import numpy as np
import pytest

from scicamera import Camera, CameraConfig, FakeCamera
from scicamera.testing import mature_after_frames_or_timeout


@pytest.mark.parametrize("CameraClass", [Camera, FakeCamera])
def test_capture_file_encodings(CameraClass: Type[Camera]):
    """Capture a np.array directly from the camera."""
    with CameraClass() as camera:
        preview_config = CameraConfig.for_preview(camera, main={"size": (800, 600)})
        camera.configure(preview_config)
        camera.start()
        mature_after_frames_or_timeout(camera)
        array = camera.capture_array().result()
        assert isinstance(array, np.ndarray)
        camera.stop()



@pytest.mark.parametrize("CameraClass", [Camera, FakeCamera])
def test_capture_array_mode_change(CameraClass: Type[Camera]):
    with CameraClass() as camera:
        camera.start_preview()

        preview_config = CameraConfig.for_preview(camera)
        still_config = CameraConfig.for_still(camera)
        camera.configure(preview_config)

        camera.start()
        camera.discard_frames(2)
        array = camera.capture_array(config=still_config).result()
        assert array.shape == camera.sensor_resolution[::-1] + (3,)
