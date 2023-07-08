#!/usr/bin/python3
# Capture a DNG and a JPEG made from the same raw data.
import os
import tempfile
from typing import Type

import pytest

from scicamera import Camera, FakeCamera
from scicamera.configuration import CameraConfig


@pytest.mark.parametrize("CameraClass", [Camera, FakeCamera])
def test_capture_request_encode(CameraClass: Type[Camera]):
    with CameraClass() as camera:
        camera.start_runloop()

        preview_config = CameraConfig.for_preview(camera)
        camera.configure(preview_config)

        camera.start()
        camera.discard_frames(2)

        capture_config = CameraConfig.for_still(camera)
        camera.switch_mode(capture_config).result()
        request = camera.capture_request(capture_config).result()

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "capture.jpg")
            request.make_image("main").convert("RGB").save(path)
            assert os.path.isfile(path)
        request.release()
