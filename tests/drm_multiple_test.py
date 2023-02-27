import time

import pytest

from scicamera import Camera, CameraInfo
from scicamera.testing import elapse_frames_or_timeout


@pytest.mark.skipif(CameraInfo.n_cameras() <= 1, reason="Test requires two cameras")
def test_multicamera():
    camera1 = Camera(0)
    camera1.start_preview()
    camera1.start()
    elapse_frames_or_timeout(camera1, 10, 1)

    camera2 = Camera(1)
    camera2.start_preview()
    camera2.start()
    elapse_frames_or_timeout(camera2, 10, 1)

    camera1.close()
    camera1 = Camera(0)
    camera1.start_preview()
    camera1.start()
    elapse_frames_or_timeout(camera1, 10, 1)

    camera2.close()
    camera2 = Camera(1)
    camera2.start_preview()
    camera2.start()
    elapse_frames_or_timeout(camera2, 10, 1)

    camera1.close()
    camera2.close()
