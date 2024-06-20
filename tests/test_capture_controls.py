from typing import Type

import pytest

from scicamera import Camera, CameraConfig
from scicamera.controls import Controls
from scicamera.fake import FakeCamera
from scicamera.testing import requires_controls


@pytest.mark.parametrize("CameraClass", [Camera, FakeCamera])
def test_changes_controls(CameraClass: Type[Camera]):
    with CameraClass() as camera:
        requires_controls(camera, ("ExposureTime", "AnalogueGain"))
        camera.start_runloop()

        preview_config = CameraConfig.for_preview(camera)
        camera.configure(preview_config)

        camera.start()
        camera.discard_frames(2)

        controls = Controls(camera)
        controls.AnalogueGain = 1.0
        controls.ExposureTime = 10000

        camera.set_controls(controls)
        camera.discard_frames(2).result()
