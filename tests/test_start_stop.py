from typing import Type

import pytest

from scicamera import Camera, FakeCamera


@pytest.mark.parametrize("CameraClass", [Camera, FakeCamera])
def test_start_stop_runloop(CameraClass: Type[Camera]):
    camera = CameraClass()
    camera.start()
    camera.discard_frames(2).result(timeout=0.1)

    for _ in range(2):
        camera.stop_preview()
        camera.start_preview()

    camera.discard_frames(2).result(timeout=0.1)
    camera.stop()
    camera.close()


@pytest.mark.parametrize("CameraClass", [Camera, FakeCamera])
def test_start_stop(CameraClass: Type[Camera]):
    camera = CameraClass()
    for _ in range(3):
        camera.start()
        camera.discard_frames(2).result(timeout=0.1)
        camera.stop()
    camera.close()
