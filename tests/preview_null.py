#!/usr/bin/python3

from picamera2 import CameraConfig, Picamera2

camera = Picamera2()
config = CameraConfig.create_preview_configuration(camera)
camera.configure(config)

camera.start()
camera.discard_frames(4).result()
camera.stop()
