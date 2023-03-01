from typing import Type

import pytest

from scicamera import Camera, CameraConfig, FakeCamera


@pytest.mark.parametrize("config_method", [CameraConfig.for_preview, CameraConfig.for_video, CameraConfig.for_still])
@pytest.mark.parametrize("CameraClass", [Camera, FakeCamera])
def test_capture_config_video(CameraClass: Type[Camera], config_method):
    camera = CameraClass()
    config = config_method(camera)
    camera.configure(config)
    camera.start()
    camera.discard_frames(2).result()
    camera.stop()
    camera.close()
