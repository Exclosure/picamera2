from scicamera.fake import FakeCamera
from scicamera.testing import mature_after_frames_or_timeout

def test_fake_camera_init():
    camera = FakeCamera()
    camera.start()

    mature_after_frames_or_timeout(camera, 10, 1)
    camera.stop()
    camera.close()
