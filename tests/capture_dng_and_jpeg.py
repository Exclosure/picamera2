#!/usr/bin/python3
# Capture a DNG and a JPEG made from the same raw data.
from picamera2 import Picamera2
from picamera2.configuration import CameraConfiguration

camera = Picamera2()
camera.start_preview()

preview_config = CameraConfiguration.create_preview_configuration(camera)
camera.configure("preview")

camera.start()
camera.discard_frames(2)

capture_config = CameraConfiguration.create_still_configuration(camera, raw={})
camera.switch_mode(capture_config).result()
request = camera.capture_request(capture_config).result()
request.make_image("main").convert("RGB").save("full.jpg")
request.release()

camera.close()
