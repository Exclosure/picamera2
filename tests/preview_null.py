#!/usr/bin/python3

from picamera2 import Picamera2, CameraConfiguration

camera = Picamera2()
config = CameraConfiguration.create_preview_configuration(camera)
camera.configure(config)

camera.start()
camera.discard_frames(4).result()
camera.stop()
