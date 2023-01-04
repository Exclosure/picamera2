#!/usr/bin/python3

# Test that we can successfully close a QtGlPreview window and open a new one.
from picamera2 import Picamera2, CameraConfiguration

for i in range(2):
    print(f"{i} preview...")
    camera = Picamera2()
    camera.configure(CameraConfiguration.create_preview_configuration(camera))
    camera.start_preview()
    camera.start()
    camera.discard_frames(5).result()
    camera.close()
    print("Done")
