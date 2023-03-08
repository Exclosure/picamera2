from typing import Type

import pytest

from scicamera import Camera, CameraConfig
from scicamera.fake import FakeCamera


@pytest.mark.parametrize("CameraClass", [Camera, FakeCamera])
def test_config_preview(CameraClass: Type[Camera]):
    camera = CameraClass()

    # We're going to set up some configuration structures, apply each one in
    # turn and see if it gave us the configuration we expected.

    # Preview
    cfg_preview = CameraConfig.for_preview(camera)
    cfg_preview.size = (800, 600)
    cfg_preview.format = "RGB888"
    cfg_preview.controls.ExposureTime = 10000

    camera.configure(cfg_preview)
    assert camera.controls.ExposureTime == 10000

    camera.close()


@pytest.mark.parametrize("CameraClass", [Camera, FakeCamera])
def test_config_video(CameraClass: Type[Camera]):
    camera = CameraClass()
    # Video
    cfg_video = CameraConfig.for_video(camera)
    cfg_video.main.format = "YUV420"

    has_frameduration = (
        "FrameDurationLimits" in camera.controls.available_control_names()
    )
    if has_frameduration:
        cfg_video.controls.set_frame_rate(25.0)

    camera.configure(cfg_video)

    if has_frameduration:
        frame_rate = camera.controls.get_frame_rate()
        assert frame_rate == pytest.approx(frame_rate, 25.0, 0.1)

    camera.close()

@pytest.mark.parametrize("CameraClass", [Camera, FakeCamera])
def test_config_still(CameraClass: Type[Camera]):
    camera = CameraClass()

    if camera.sensor_format == "MJPEG":
        camera.close()
        pytest.skip("MJPEG cameras don't support still capture")

    # Still
    cfg_still = CameraConfig.for_still(camera)
    cfg_still.size = (1024, 768)
    cfg_still.enable_lores()
    cfg_still.lores.format = "YUV420"
    cfg_still.enable_raw()

    config = camera.camera_configuration()  
    half_res = tuple([v // 2 for v in camera.sensor_resolution])
    cfg_still.raw.size = half_res

    camera.configure(cfg_still)
    config = camera.camera_configuration()
    try:
        assert config.raw.size == half_res
        assert config.lores.format == "YUV420"
    finally:
        camera.close()
