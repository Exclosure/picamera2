#!/usr/bin/python3
# Capture a PNG while still running in the preview mode.

from picamera2 import Picamera2, CameraConfiguration

camera = Picamera2()
camera.start_preview()

preview_config = CameraConfiguration.create_preview_configuration(camera, main={"size": (800, 600)})
camera.configure(preview_config)

camera.start()
camera.discard_frames(2)
camera.capture_file("test.png").result()
camera.close()
