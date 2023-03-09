from typing import Type

import pytest

from scicamera import Camera, FakeCamera
from scicamera.camera import CameraManager
from scicamera.configuration import CameraConfig
from scicamera.testing import mature_after_frames_or_timeout


@pytest.mark.parametrize("CameraClass", [Camera, FakeCamera])
def test_capture_metadata(CameraClass: Type[Camera]):
    with CameraClass() as camera:
        camera.start_preview()

        preview_config = CameraConfig.for_preview(camera)
        camera.configure(preview_config)

        camera.start()
        mature_after_frames_or_timeout(camera)
        print(camera.capture_metadata().result(timeout=1.0))


@pytest.mark.parametrize("CameraClass", [Camera, FakeCamera])
def test_capture_metadata_deserializes(CameraClass: Type[Camera]):
    with CameraClass() as camera:
        camera.start_preview()

        preview_config = CameraConfig.for_preview(camera)
        camera.configure(preview_config)

        camera.start()
        mature_after_frames_or_timeout(camera)
        metadata = camera.capture_metadata().result(timeout=1.0)

    if "ColourGains" in metadata:
        assert len(metadata["ColourGains"]) == 2

    if "ColourCorrectionMatrix" in metadata:
        assert len(metadata["ColourCorrectionMatrix"]) == 9
