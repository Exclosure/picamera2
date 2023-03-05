#!/usr/bin/python3

# Use the configuration structure method to do a full res capture.
from scicamera import Camera, CameraConfig

camera = Camera()

# We don't really need to change anything, but let's mess around just as a test.
video_configuration = CameraConfig.for_video(camera)
video_configuration.size = (800, 480)
video_configuration.format = "YUV420"

camera.start()
camera.discard_frames(2).result()
camera.stop()
