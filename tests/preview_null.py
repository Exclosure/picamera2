#!/usr/bin/python3

from scicamera import CameraConfig, Camera

camera = Camera()
config = CameraConfig.for_preview(camera)
camera.configure(config)

camera.start()
camera.discard_frames(4).result()
camera.stop()
