#!/usr/bin/python3
# Capture a DNG and a JPEG made from the same raw data.
from picamera2 import Picamera2

camera = Picamera2()
camera.start_preview()

preview_config = camera.create_preview_configuration()
capture_config = camera.create_still_configuration(raw={})
camera.configure(preview_config)

camera.start()
camera.discard_frames(2)
request = camera.switch_mode_capture_request_and_stop(capture_config)
request.make_image("main").convert('RGB').save("full.jpg")
request.release()

camera.close()
