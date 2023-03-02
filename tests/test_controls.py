from pprint import pprint
from typing import Type

import pytest

from scicamera import Camera, CameraConfig, FakeCamera
from scicamera.fake import FakeCamera

from scicamera.testing import mature_after_frames_or_timeout

@pytest.mark.parametrize("CameraClass", [Camera, FakeCamera])
def test_set_controls(CameraClass: Type[Camera]):
    camera = CameraClass()
    camera.start_preview()

    preview_config = CameraConfig.for_preview(camera)
    camera.configure(preview_config)

    camera.start()
    mature_after_frames_or_timeout(2)

    if {"AwbEnable", "AeEnable"} <= camera.controls.available_control_names():
        camera.set_controls({"AwbEnable": 0, "AeEnable": 0})
    mature_after_frames_or_timeout(2)
    camera.close()


@pytest.mark.parametrize("CameraClass", [Camera, FakeCamera])
def test_set_gain_exposure(CameraClass: Type[Camera]):
    """Example of setting controls.

    Here, after one second, we fix the AGC/AEC to the values it
    has reached whereafter it will no longer change.
    """
    camera = CameraClass()
    available_controls = camera.controls.available_control_names()

    if not {"ExposureTime", "AnalogueGain", "ColourGains"}.issubset(available_controls):
        camera.close()
        pytest.skip(f"This camera {camera} does not support setting gain/exposure")

    camera.start_preview()

    preview_config = CameraConfig.for_preview(camera)
    camera.configure(preview_config)

    camera.start()
    mature_after_frames_or_timeout(2)
    metadata = camera.capture_metadata().result(timeout=0.5)
    pprint(metadata)
    controls = {c: metadata[c] for c in ["ExposureTime", "AnalogueGain", "ColourGains"]}
    print(controls)

    camera.controls.set_controls(controls)
    mature_after_frames_or_timeout(2)

    camera.close()


@pytest.mark.parametrize("CameraClass", [FakeCamera])
def test_set_frame_rate(CameraClass: Type[Camera]):
    camera = CameraClass()
    camera.start()
    camera.controls.FrameRate = 30
    camera.stop()
    camera.close()
