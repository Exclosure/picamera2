from typing import Type

import pytest

from scicamera import Camera, CameraConfig, FakeCamera


@pytest.mark.parametrize("CameraClass", [Camera, FakeCamera])
def test_set_controls(CameraClass: Type[Camera]):
    camera = CameraClass()
    camera.start_preview()

    preview_config = CameraConfig.for_preview(camera)
    camera.configure(preview_config)

    camera.start()
    camera.discard_frames(2)

    if {"AwbEnable", "AeEnable"} <= camera.controls.available_control_names():
        camera.set_controls({"AwbEnable": 0, "AeEnable": 0})
    camera.discard_frames(2).result()
    camera.close()
