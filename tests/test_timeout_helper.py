import pytest

from scicamera import Camera
from scicamera.testing import mature_after_frames_or_timeout


def test_timeout_helper():
    camera = Camera()
    with pytest.raises(TimeoutError):
        mature_after_frames_or_timeout(camera, 10, 0.1).result()

    camera.start()
    mature_after_frames_or_timeout(camera, 2, 5).result()
    camera.stop()
