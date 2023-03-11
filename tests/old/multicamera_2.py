#!/usr/bin/python3
from scicamera import Camera, CameraConfig, CameraInfo
from scicamera.testing import mature_after_frames_or_timeout

if CameraInfo.n_cameras() <= 1:
    print("SKIPPED (one camera)")
    quit()

with Camera(0) as camera1:
    config1 = CameraConfig.for_preview(camera1)
    camera1.configure(config1)
    camera1.start_preview()
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
