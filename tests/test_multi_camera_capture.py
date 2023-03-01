from typing import Type

import pytest

from scicamera import Camera, FakeCamera
from scicamera.camera import CameraManager


@pytest.mark.parametrize("CameraClass", [Camera, FakeCamera])
def test_capture_multi_camera(CameraClass: Type[Camera]):
    n_cameras = len(CameraManager.singleton().cms.cameras)
    for index in range(n_cameras):
        camera = CameraClass(camera_num=index)
        camera.start()
        camera.discard_frames(2).result(timeout=1.0)
        camera.stop()
        camera.close()
