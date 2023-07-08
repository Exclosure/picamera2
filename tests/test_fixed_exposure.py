from typing import Type

import pytest

from scicamera import Camera, CameraConfig
from scicamera.fake import FakeCamera


@pytest.mark.parametrize("CameraClass", [Camera, FakeCamera])
def test_fixed_exposure(CameraClass: Type[Camera]):
    # Start camera with fixed exposure and gain.
    with Camera() as camera:
        camera.start_runloop()

        if {"ExposureTime", "AnalogueGain"} < camera.controls.available_control_names():
            controls = {"ExposureTime": 10000, "AnalogueGain": 1.0}
            preview_config = CameraConfig.for_preview(camera, controls=controls)
        else:
            preview_config = CameraConfig.for_preview(camera)

        camera.configure(preview_config)

        camera.start()
        camera.discard_frames(2).result()
        camera.stop()
