from typing import Type

import pytest

from scicamera import Camera, CameraConfig, FakeCamera
from scicamera.testing import mature_after_frames_or_timeout


@pytest.mark.parametrize("CameraClass", [Camera, FakeCamera])
def test_context_manager(CameraClass: Type[Camera]):
    print("With context...")
    with CameraClass() as camera:
        config = CameraConfig.for_preview(camera)
        camera.configure(config)
        camera.start()
        metadata = camera.capture_metadata().result()
        assert isinstance(metadata, dict)
        print(metadata)

    print("Without context...")
    camera = CameraClass()
    config = CameraConfig.for_preview(camera)
    camera.configure(config)
    camera.start()
    metadata = camera.capture_metadata().result()
    print(metadata)
    camera.stop_preview()
    camera.close()
