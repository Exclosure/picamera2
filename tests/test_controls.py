from typing import Type

import pytest

from scicamera import Camera, CameraConfig, FakeCamera
from pprint import pprint

from scicamera import Camera, CameraConfig
from scicamera.fake import FakeCamera
from typing import Type

import pytest

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
    camera.discard_frames(2)
    metadata = camera.capture_metadata().result(timeout=0.5)
    pprint(metadata)
    controls = {
        c: metadata[c]
        for c in ["ExposureTime", "AnalogueGain", "ColourGains"]
    }
    print(controls)

    camera.controls.set_controls(controls)
    camera.discard_frames(2)

    camera.close()
