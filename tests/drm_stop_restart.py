from scicamera import Camera
from scicamera.testing import mature_after_frames_or_timeout


def test_restart(camera: Camera):
    camera.start_preview()
    camera.start()
    camera.discard_frames(2).result()
    camera.stop_preview()

    mature_after_frames_or_timeout(camera, 2, 1).result()

    camera.start_preview()
    camera.discard_frames(2).result()
    camera.stop()
    camera.stop_preview()
