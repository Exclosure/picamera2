#!/usr/bin/python3
# Capture a DNG.

from picamera2 import Picamera2

camera = Picamera2()
camera.start_preview()

preview_config = camera.create_preview_configuration()
capture_config = camera.create_still_configuration(raw={})
camera.configure(preview_config)

with camera:
    camera.discard_frames(2)
    camera.capture_file("full.dng", name="raw", config=capture_config).result()
