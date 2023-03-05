from typing import Type

import pytest

from scicamera import Camera, FakeCamera
from scicamera.camera import CameraManager
from scicamera.testing import mature_after_frames_or_timeout


@pytest.mark.parametrize("CameraClass", [Camera, FakeCamera])
def test_capture_multi_camera(CameraClass: Type[Camera]):
    n_cameras = len(CameraManager.singleton().cms.cameras)
    for index in range(n_cameras):
        camera = CameraClass(camera_num=index)
        camera.start()
        mature_after_frames_or_timeout(camera)
        camera.stop()
        camera.close()
