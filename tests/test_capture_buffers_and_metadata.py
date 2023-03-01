
from scicamera import Camera, CameraConfig
from scicamera.configuration import CameraConfig
from scicamera.testing import mature_after_frames_or_timeout

from typing import Type
from scicamera import Camera, FakeCamera

import pytest

@pytest.mark.parametrize("CameraClass", [Camera, FakeCamera])
def test_capture_buffers_and_metadata(CameraClass: Type[Camera]):
    camera = CameraClass()
    camera.start_preview()

    preview_config = CameraConfig.for_preview(camera)
    capture_config = CameraConfig.for_still(camera, raw={})
    camera.configure(preview_config)

    camera.start()
    mature_after_frames_or_timeout(camera, 2).result()
    camera.switch_mode(capture_config).result()
    buffers, metadata = camera.capture_buffers_and_metadata(["main", "raw"]).result()

    assert isinstance(buffers, list)
    assert len(buffers) == 2
    assert isinstance(metadata, dict)

    camera.stop()
    camera.close()
