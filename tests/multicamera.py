#!/usr/bin/python3

import concurrent.futures

from picamera2 import CameraConfiguration, CameraInfo, Picamera2

if CameraInfo.n_cameras() <= 1:
    print("SKIPPED (one camera)")
    quit()

camera1 = Picamera2(0)
camera1.configure(CameraConfiguration.create_preview_configuration(camera1))
camera1.start()

camera2 = Picamera2(1)
camera2.configure(CameraConfiguration.create_preview_configuration(camera2))
camera2.start()

f1 = camera1.discard_frames(4)
f2 = camera2.discard_frames(4)
concurrent.futures.wait((f1, f2), timeout=5)

md1 = camera1.capture_metadata()
md2 = camera2.capture_metadata()
concurrent.futures.wait((md1, md2), timeout=10)
print(md1.result())
print(md2.result())

fi1 = camera1.capture_file("testa.jpg")
fi2 = camera2.capture_file("testb.jpg")
concurrent.futures.wait((fi1, fi2), timeout=10)

camera1.stop()
camera2.stop()

camera1.close()
camera2.close()
