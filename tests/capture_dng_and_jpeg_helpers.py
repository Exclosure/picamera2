#!/usr/bin/python3
# Capture a DNG and a JPEG made from the same raw data.
from picamera2 import Picamera2, CameraConfiguration
from picamera2.configuration import CameraConfiguration
from picamera2.testing import mature_after_frames_or_timeout

camera = Picamera2()
camera.start_preview()

preview_config = CameraConfiguration.create_preview_configuration(camera)
capture_config = CameraConfiguration.create_still_configuration(camera, raw={})
camera.configure(preview_config)

camera.start()
mature_after_frames_or_timeout(camera, 2).result()
camera.switch_mode(capture_config).result()
buffers, metadata = camera.capture_buffers_and_metadata(["main", "raw"]).result()

camera.stop()
camera.close()
