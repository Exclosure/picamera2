from scicamera import Camera
from scicamera.testing import elapse_frames_or_timeout


def test_restart(camera: Camera):
    camera.start_preview()
    camera.start()
    elapse_frames_or_timeout(camera, 2, 1)
    camera.stop_preview()

    camera.start_preview()
    elapse_frames_or_timeout(camera, 2, 1)
    camera.stop()
    camera.stop_preview()
