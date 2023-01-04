#!/usr/bin/python3

# For use from the login console, when not running X Windows.
from picamera2 import CameraConfiguration, Picamera2

camera = Picamera2()
camera.start_preview()

preview_config = CameraConfiguration.create_preview_configuration(
    camera, {"size": (640, 360)}
)
camera.configure(preview_config)

camera.start()
camera.discard_frames(2).result()
camera.stop()
camera.close()
