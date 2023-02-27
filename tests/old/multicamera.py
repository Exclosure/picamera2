import concurrent.futures
import os
import tempfile

import pytest

from scicamera import Camera, CameraConfig, CameraInfo


@pytest.mark.skipif(CameraInfo.n_cameras() <= 1, reason="Test requires two cameras")
def test_multicamera_preview_3():
    camera1 = Camera(0)
    camera1.configure(CameraConfig.for_preview(camera1))
    camera1.start()

    camera2 = Camera(1)
    camera2.configure(CameraConfig.for_preview(camera2))
    camera2.start()

    f1 = camera1.discard_frames(4)
    f2 = camera2.discard_frames(4)
    concurrent.futures.wait((f1, f2), timeout=5)

    md1 = camera1.capture_metadata()
    md2 = camera2.capture_metadata()
    concurrent.futures.wait((md1, md2), timeout=10)
    print(md1.result())
    print(md2.result())

    with tempfile.TemporaryDirectory() as tmpdir:
        file1 = tmpdir + "/testa.jpg"
        file2 = tmpdir + "/testb.jpg"
        fi1 = camera1.capture_file(file1)
        fi2 = camera2.capture_file(file2)
        concurrent.futures.wait((fi1, fi2), timeout=10)
        assert os.path.exists(file1)
        assert os.path.exists(file2)

    camera1.stop()
    camera2.stop()

    camera1.close()
    camera2.close()
