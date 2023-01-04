#!/usr/bin/python3
# Capture a JPEG while still running in the preview mode.
from picamera2 import Picamera2, CameraConfiguration

from picamera2.configuration import CameraConfiguration

camera = Picamera2()
camera.start_preview()

preview_config = CameraConfiguration.create_preview_configuration(camera)
capture_config = CameraConfiguration.create_still_configuration(camera)
camera.configure(preview_config)

camera.start()
camera.discard_frames(2)
camera.capture_file("test_full.jpg", config=capture_config).result()
camera.close()
