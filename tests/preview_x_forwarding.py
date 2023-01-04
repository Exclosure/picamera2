#!/usr/bin/python3

# The QtPreview uses software rendering and thus makes more use of the
# CPU, but it does work with X forwarding, unlike the QtGlPreview.

from picamera2 import CameraConfiguration, Picamera2

camera = Picamera2()
camera.start_preview()

preview_config = CameraConfiguration.create_preview_configuration(camera)
camera.configure(preview_config)

camera.start()
camera.discard_frames(2).result()
camera.stop()

camera.close()
