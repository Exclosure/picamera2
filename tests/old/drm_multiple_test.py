from scicamera import Camera, CameraInfo
from scicamera.testing import mature_after_frames_or_timeout
import time


if CameraInfo.n_cameras < 2:
    print("SKIPPED (one camera)")
    quit()

with Camera(0) as camera1:
    camera1.start_runloop()
    camera1.start()
    mature_after_frames_or_timeout(camera1)

    with Camera(1) as camera2:
        camera2.start_runloop()
        camera2.start()
        mature_after_frames_or_timeout(camera2)

    with Camera(1) as camera2:
        camera2 = Camera(1)
        camera2.start_runloop()
        camera2.start()
        mature_after_frames_or_timeout(camera2)
        camera2.close()
