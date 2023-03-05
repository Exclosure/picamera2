from concurrent.futures import Future, wait
from typing import Type

import pytest

from scicamera import Camera, FakeCamera
from scicamera.frame import CameraFrame
from scicamera.testing import mature_after_frames_or_timeout


@pytest.mark.parametrize("CameraClass", [Camera, FakeCamera])
def test_capture_multi_frame(CameraClass: Type[Camera]):
    camera = CameraClass()

    if "FrameDurationLimits" not in camera.controls.available_control_names():
        camera.close()
        pytest.skip("Camera does not support multi-frame capture.")

    camera.start()
    camera.controls.ExposureTime = 10000
    mature_after_frames_or_timeout(camera)
    futures = camera.capture_serial_frames(5)
    wait(futures, timeout=10)

    camera.stop()
    camera.close()

    for f in futures:
        frame = f.result()
        assert isinstance(f, Future), type(f)
        assert isinstance(frame, CameraFrame), type(frame)
        assert "FrameDurationLimits" in frame.controls, frame.controls
