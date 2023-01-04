#!/usr/bin/python3

# Obtain the current camera control values in the image metadata.
from picamera2 import Picamera2, CameraConfiguration

camera = Picamera2()
camera.start_preview()

preview_config = CameraConfiguration.create_preview_configuration(camera)
camera.configure(preview_config)

camera.start()
camera.discard_frames(2)
print(camera.capture_metadata().result())
camera.close()
