from concurrent.futures import Future, wait

from scicamera import Camera
from scicamera.frame import CameraFrame

from typing import Type

import pytest

from scicamera import FakeCamera

@pytest.mark.parametrize("CameraClass", [Camera, FakeCamera])
def test_capture_multi_frame(CameraClass: Type[Camera]):
    camera = CameraClass()

    camera.start()
    futures = camera.capture_serial_frames(5)
    wait(futures, timeout=10)

    camera.stop()
    camera.close()

    for f in futures:
        assert isinstance(f, Future)
        assert isinstance(f.result(), CameraFrame)
