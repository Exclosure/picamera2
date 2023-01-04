#!/usr/bin/python3
# Capture a full resolution image to memory rather than to a file.
from PIL import Image

from picamera2 import Picamera2, CameraConfiguration
from picamera2.testing import mature_after_frames_or_timeout

camera = Picamera2()
camera.start_preview()
preview_config = CameraConfiguration.create_preview_configuration(camera)
capture_config = CameraConfiguration.create_still_configuration(camera)

camera.configure(preview_config)
camera.start()
mature_after_frames_or_timeout(camera, 5).result()

image = camera.capture_image(config=capture_config).result()
assert isinstance(image, Image.Image)

mature_after_frames_or_timeout(camera, 5).result()

camera.close()
