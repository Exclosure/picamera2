from logging import getLogger

import numpy as np

from scicamera import Camera, CameraConfig


def test_capture_array(camera: Camera):
    preview = CameraConfig.for_preview(camera)
    camera.configure(preview)
    camera.start()
    np_array = camera.capture_array().result()
    assert isinstance(np_array, np.ndarray)
    camera.stop()
