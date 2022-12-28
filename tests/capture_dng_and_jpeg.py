#!/usr/bin/python3
# Capture a DNG and a JPEG made from the same raw data.
from picamera2 import Picamera2
from picamera2.testing import mature_after_frames_or_timeout

camera = Picamera2()
camera.start_preview()

preview_config = camera.create_preview_configuration()
capture_config = camera.create_still_configuration(raw={})
camera.configure(preview_config)

camera.start()
camera.discard_frames(2)
camera.switch_mode_async(capture_config)
request_fut = camera.capture_request_async()
camera.stop_async()

request = request_fut.result()
request.save("main", "full.jpg")
request.release()

camera.close()
