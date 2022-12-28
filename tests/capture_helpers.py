#!/usr/bin/python3
# Capture multiple representations of a captured frame.
from picamera2 import Picamera2
from picamera2.helpers import Helpers

camera = Picamera2()
camera.start_preview()

preview_config = camera.create_preview_configuration()
capture_config = camera.create_still_configuration(raw={})
camera.configure(preview_config)

camera.start()
camera.discard_frames(2)
camera.switch_mode_async(capture_config)
buffers, metadata = camera.capture_buffers_and_metadata("main")

arr = Helpers.make_array(buffers[0], capture_config["main"])
image = Helpers.make_image(buffers[0], capture_config["main"])

camera.close()
