from concurrent.futures import wait

import pytest

from scicamera import Camera, CameraConfig, CameraInfo
from scicamera.testing import mature_after_frames_or_timeout


@pytest.mark.skipif(CameraInfo.n_cameras() <= 1, reason="Requires multiple cameras.")
def test_multicamera_interleve():
    camera1 = Camera(0)
    camera1.configure(CameraConfig.for_preview(camera1))
    camera1.start()

    camera2 = Camera(1)
    camera2.configure(CameraConfig.for_preview(camera2))
    camera2.start()

    f1 = camera1.discard_frames(4)
    f2 = camera2.discard_frames(4)
    wait((f1, f2), timeout=5)

    md1 = camera1.capture_metadata()
    md2 = camera2.capture_metadata()
    wait((md1, md2), timeout=10)
    print(md1.result())
    print(md2.result())

    fi1 = camera1.capture_file("testa.jpg")
    fi2 = camera2.capture_file("testb.jpg")
    wait((fi1, fi2), timeout=10)

    camera1.stop()
    camera2.stop()

    camera1.close()
    camera2.close()


@pytest.mark.skipif(CameraInfo.n_cameras() <= 1, reason="Requires multiple cameras.")
def test_multicamera_context():
    with Camera(0) as camera1:
        config1 = CameraConfig.for_preview(camera1)
        camera1.start_runloop()
        camera1.configure(config1)
        camera1.start()
        mature_after_frames_or_timeout(camera1)

        with Camera(1) as camera2:
            config2 = CameraConfig.for_preview(camera2)
            camera2.configure(config2)
            camera2.start()
            mature_after_frames_or_timeout(camera2)
        camera1.stop()

    mature_after_frames_or_timeout(camera1)
    camera2.capture_file("testb.jpg").result()
    camera2.stop()
    

@pytest.mark.skipif(CameraInfo.n_cameras() <= 1, reason="Requires multiple cameras.")
def test_multi_camera_close():
    with Camera(0) as camera1:
        camera1.start()
        mature_after_frames_or_timeout(camera1)

        with Camera(1) as camera2:
            camera2.start()
            mature_after_frames_or_timeout(camera2)

        with Camera(1) as camera2:
            camera2.start()
            mature_after_frames_or_timeout(camera2)
            camera2.close()
