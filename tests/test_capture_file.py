import os
from tempfile import TemporaryDirectory
from typing import Type

import pytest

from scicamera import Camera, CameraConfig, FakeCamera
from scicamera.testing import mature_after_frames_or_timeout


@pytest.mark.parametrize("extension", ["jpg", "png", "bmp", "gif", "pgm"])
@pytest.mark.parametrize("CameraClass", [Camera, FakeCamera])
def test_capture_file_encodings(CameraClass: Type[Camera], extension: str):
    """Capture a JPEG while still running in the preview mode.

    When you capture to a file, the return value is the metadata for that image.
    """
    with CameraClass() as camera:

        preview_config = CameraConfig.for_preview(camera, main={"size": (800, 600)})
        camera.configure(preview_config)

        camera.start_preview()

        camera.start()
        mature_after_frames_or_timeout(camera)
        with TemporaryDirectory() as tmpdir:
            filepath = f"{tmpdir}/test.{extension}"
            metadata = camera.capture_file(filepath).result()
            assert os.path.isfile(filepath)

        print(metadata)
        camera.stop()
