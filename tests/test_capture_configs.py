from typing import Type

import pytest

from scicamera import Camera, CameraConfig, FakeCamera


@pytest.mark.parametrize("CameraClass", [Camera, FakeCamera])
def test_capture_config_video(CameraClass: Type[Camera]):
    camera = CameraClass()
    video_config = CameraConfig.for_video(camera)
    camera.configure(video_config)
    camera.start()
    camera.discard_frames(2).result()
    camera.stop()
    camera.close()


@pytest.mark.parametrize("CameraClass", [Camera, FakeCamera])
def test_capture_config_still(CameraClass: Type[Camera]):
    camera = CameraClass()
    still_config = CameraConfig.for_still(camera)
    camera.configure(still_config)
    camera.start()
    camera.discard_frames(2).result()
    camera.stop()
    camera.close()
