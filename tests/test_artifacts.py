import os
from typing import Type

import numpy as np
import pytest

from scicamera import Camera, CameraConfig, FakeCamera
from scicamera.testing import mature_after_frames_or_timeout

# This test is a bit unusual. It captures the raw arrays and
# exports them as npy files. These files are then loaded and
# archived into githubs artifacts system. This allows to visually
# check the raw arrays for correctness.


@pytest.mark.parametrize("CameraClass", [Camera, FakeCamera])
def test_capture_file_encodings(CameraClass: Type[Camera]):
    if not os.path.isdir("artifacts"):
        os.mkdir("artifacts")

    with CameraClass() as camera:
        preview_config = CameraConfig.for_still(camera, main={})
        preview_config.enable_raw()
        camera.configure(preview_config)

        camera.start()

        for stream_name in ("main", "raw"):
            mature_after_frames_or_timeout(camera)
            array = camera.capture_array(name=stream_name).result()
            np.save(f"artifacts/image-{stream_name}-0.npy", array)

            bytez = camera.capture_buffer(name=stream_name).result()
            np.save(f"artifacts/bytes-{stream_name}-0.npy", bytez)

        camera.stop()
