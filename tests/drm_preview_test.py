#!/usr/bin/python3

# Test that we can successfully close a QtGlPreview window and open a new one.

from picamera2 import CameraConfiguration, Picamera2

print("First preview...")
camera = Picamera2()
camera.configure(CameraConfiguration.create_preview_configuration(camera))
camera.start_preview()
camera.start()
camera.discard_frames(2).result()
camera.close()
print("Done")

print("Second preview...")
camera = Picamera2()
camera.configure(CameraConfiguration.create_preview_configuration(camera))
camera.start_preview()
camera.start()
camera.discard_frames(2).result()
camera.close()
print("Done")
