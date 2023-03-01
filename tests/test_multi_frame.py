from concurrent.futures import Future, wait
from typing import Type

import pytest

from scicamera import Camera, FakeCamera
from scicamera.frame import CameraFrame


@pytest.mark.parametrize("CameraClass", [Camera, FakeCamera])
def test_capture_multi_frame(CameraClass: Type[Camera]):
    camera = CameraClass()

    camera.start()
    futures = camera.capture_serial_frames(5)
    wait(futures, timeout=10)

    camera.stop()
    camera.close()

    for f in futures:
        frame = f.result()
        assert isinstance(f, Future)
        assert isinstance(frame, CameraFrame)
        assert frame.controls["ExposureTime"] is not None
