#!/usr/bin/python3

# Capture a DNG.

import time

from picamera2 import Picamera2
from picamera2.testing import mature_after_frames_or_timeout

camera = Picamera2()
camera.start_preview()

preview_config = camera.create_preview_configuration()
capture_config = camera.create_still_configuration(raw={})
camera.configure(preview_config)

with camera:
    camera.discard_frames(2)
    camera.switch_mode_and_capture_file(capture_config, "full.dng", name="raw")

