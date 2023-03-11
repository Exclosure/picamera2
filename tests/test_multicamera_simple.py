from concurrent.futures import wait
from typing import Type

import pytest

from scicamera import Camera, CameraConfig, CameraManager, FakeCamera


def _n_camera_run(n: int, CameraClass: Type[Camera]):
    cameras = [CameraClass(i) for i in range(n)]
    for camera in cameras:
        camera.configure(CameraConfig.for_preview(camera))
        camera.start_preview()
        camera.start()

    futs = []
    for camera in cameras:
        futs.append(camera.discard_frames(2))

    wait(futs, timeout=2.0)

    for camera in cameras:
        camera.stop()
        camera.close()


@pytest.mark.parametrize("n_cameras", [1, 2, 3, 4])
def test_fake_cameras(n_cameras: int):
    _n_camera_run(n_cameras, FakeCamera)


def test_all_real_cameras():
    n_cameras = CameraManager.singleton().n_cameras_attached()
    _n_camera_run(n_cameras, Camera)
