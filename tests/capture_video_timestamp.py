#!/usr/bin/python3
from scicamera import CameraConfig, Camera

camera = Camera()
video_config = CameraConfig.for_video(camera)
camera.configure(video_config)

camera.start()
camera.discard_frames(2).result()
camera.stop()
camera.close()
