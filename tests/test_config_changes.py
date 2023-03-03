from typing import Type

import pytest

from scicamera import Camera, CameraConfig
from scicamera.fake import FakeCamera


@pytest.mark.parametrize("CameraClass", [Camera, FakeCamera])
def test_configurations(CameraClass: Type[Camera]):
    camera = CameraClass()

    # We're going to set up some configuration structures, apply each one in
    # turn and see if it gave us the configuration we expected.

    # Preview
    cfg_preview = CameraConfig.for_preview(camera)
    cfg_preview.size = (800, 600)
    cfg_preview.format = "RGB888"
    cfg_preview.controls.ExposureTime = 10000

    camera.configure(cfg_preview)
    if camera.controls.ExposureTime != 10000:
        raise RuntimeError("exposure value was not set")

    config = camera.camera_configuration()
    if config.main.size != (800, 600):
        raise RuntimeError("preview resolution incorrect")

    # Video
    cfg_video = CameraConfig.for_video(camera)
    cfg_video.main.size = (800, 480)
    cfg_video.main.format = "YUV420"
    cfg_video.controls.FrameRate = 25.0

    camera.configure(cfg_video)
    if camera.controls.FrameRate < 24.99 or camera.controls.FrameRate > 25.01:
        raise RuntimeError("framerate was not set")

    config = camera.camera_configuration()
    if config.size != (800, 480):
        raise RuntimeError("video resolution incorrect")
    if config.format != "YUV420":
        raise RuntimeError("video format incorrect")

    # Still
    cfg_still = CameraConfig.for_still(camera)
    cfg_still.size = (1024, 768)
    cfg_still.enable_lores()
    cfg_still.lores.format = "YUV420"
    cfg_still.enable_raw()

    half_res = tuple([v // 2 for v in camera.sensor_resolution])
    cfg_still.raw.size = half_res

    camera.configure(cfg_still)
    config = camera.camera_configuration()
    if config.raw.size != half_res:
        raise RuntimeError("still raw size incorrect")

    camera.close()
