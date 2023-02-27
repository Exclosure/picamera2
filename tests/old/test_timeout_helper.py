import pytest

from scicamera import Camera
from scicamera.testing import elapse_frames_or_timeout


def test_timeout_helper():
    camera = Camera()
    with pytest.raises(TimeoutError):
        elapse_frames_or_timeout(camera, 10, 0.1)

    camera.start()
    elapse_frames_or_timeout(camera, 2, 5)
    camera.stop()
