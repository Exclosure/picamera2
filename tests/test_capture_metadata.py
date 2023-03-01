from typing import Type

import pytest

from scicamera import Camera, FakeCamera
from scicamera.camera import CameraManager
from scicamera.configuration import CameraConfig


@pytest.mark.parametrize("CameraClass", [Camera, FakeCamera])
def test_capture_metadata(CameraClass: Type[Camera]):
    camera = CameraClass()
    camera.start_preview()

    preview_config = CameraConfig.for_preview(camera)
    camera.configure(preview_config)

    camera.start()
    camera.discard_frames(2).result(timeout=1.0)
    print(camera.capture_metadata().result(timeout=1.0))
    camera.close()


@pytest.mark.parametrize("CameraClass", [Camera, FakeCamera])
def test_capture_metadata_deserializes(CameraClass: Type[Camera]):
    camera = CameraClass()
    camera.start_preview()

    preview_config = CameraConfig.for_preview(camera)
    camera.configure(preview_config)

    camera.start()
    camera.discard_frames(2).result(timeout=1.0)
    metadata = camera.capture_metadata().result(timeout=1.0)
    camera.close()

    if "ColourGains" in metadata:
        assert len(metadata["ColourGains"]) == 2

    if "ColourCorrectionMatrix" in metadata:
        assert len(metadata["ColourCorrectionMatrix"]) == 9
