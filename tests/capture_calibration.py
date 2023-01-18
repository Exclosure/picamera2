#!/usr/bin/python3
from scicamera import Camera, CameraConfig
from scicamera.timing import calibrate_camera_offset

camera = Camera()
video_config = CameraConfig.for_video(camera)
camera.configure(video_config)

camera.start()
offset = calibrate_camera_offset(camera, 20)
assert False, offset

camera.stop()
camera.close()
