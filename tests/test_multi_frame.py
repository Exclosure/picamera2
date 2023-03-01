from concurrent.futures import Future, wait
from typing import Type

import pytest

from scicamera import Camera, FakeCamera
from scicamera.frame import CameraFrame


@pytest.mark.parametrize("CameraClass", [Camera, FakeCamera])
def test_capture_multi_frame(CameraClass: Type[Camera]):
    camera = CameraClass()

    camera.start()
    camera.controls.ExposureTime = 10000
    camera.discard_frames(2).result(0.5)
    futures = camera.capture_serial_frames(5)
    wait(futures, timeout=10)

    camera.stop()
    camera.close()

    for f in futures:
        frame = f.result()
        assert isinstance(f, Future), type(f)
        assert isinstance(frame, CameraFrame), type(frame)
        assert "FrameDurationLimits" in frame.controls, frame.controls
