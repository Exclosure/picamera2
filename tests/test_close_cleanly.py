import subprocess
import sys
from typing import Type

import pytest

from scicamera import Camera, CameraManager
from scicamera.fake import FakeCamera
from scicamera.testing import requires_controls


@pytest.mark.parametrize("CameraClass", [Camera, FakeCamera])
def test_close_handlers(CameraClass: Type[Camera]):
    def run_camera():
        with CameraClass() as camera:
            camera.start()
            camera.discard_frames(2).result()
            camera.stop()

    run_camera()

    with CameraClass() as camera:
        camera.start()
        camera.stop()

    with CameraClass() as camera:
        camera.start()
        camera.discard_frames(2).result()
        camera.stop()

    if CameraManager.n_cameras_attached < 1:
        return

    # Check that everything is released so other processes can use the camera.
    program = """from scicamera import Camera
    camera = Camera()
    camera.start()
    camera.discard_frames(2)
    camera.stop()
    """
    print("Start camera in separate process:")
    cmd = ["python3", "-c", program]
    p = subprocess.Popen(cmd, stdout=sys.stdout, stderr=sys.stderr)
    assert p.wait() == 0
