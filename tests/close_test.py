import subprocess
import sys

from scicamera import Camera


def test_camera_clean_close():
    def run_camera():
        camera = Camera()
        camera.start()
        camera.discard_frames(2).result()
        camera.stop()
        camera.close()

    # First open/close several times in this process in various ways.
    run_camera()

    with Camera() as camera:
        camera.start()
        camera.discard_frames(2).result()
        camera.stop()

    camera = Camera()
    camera.start()
    camera.discard_frames(2).result()
    camera.stop()
    camera.close()

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
