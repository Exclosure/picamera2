import os
from tempfile import TemporaryDirectory

from scicamera import Camera, CameraConfig
from typing import Type
import pytest
from scicamera import FakeCamera

@pytest.mark.parametrize("extension", ["jpg", "png", "bmp", "gif", "pgm"])
@pytest.mark.parametrize("CameraClass", [Camera, FakeCamera])
def test_capture_file_encodings(CameraClass: Type[Camera], extension: str):
    """Capture a JPEG while still running in the preview mode.
    
    When you capture to a file, the return value is the metadata for that image.
    """
    camera = CameraClass()

    preview_config = CameraConfig.for_preview(camera, main={"size": (800, 600)})
    camera.configure(preview_config)

    camera.start_preview()

    camera.start()
    camera.discard_frames(2)
    with TemporaryDirectory() as tmpdir:
        filepath = f"{tmpdir}/test.{extension}"
        metadata = camera.capture_file(filepath).result()
        assert os.path.isfile(filepath)

    print(metadata)

    camera.close()
