#!/usr/bin/python3
from picamera2 import CameraConfig, Picamera2
from picamera2.testing import mature_after_frames_or_timeout

camera = Picamera2()
video_config = CameraConfig.create_video_configuration(
    camera, main={"size": (1920, 1080)}
)
camera.configure(video_config)

camera.start_preview()

camera.start()
mature_after_frames_or_timeout(camera, 5).result()

camera.stop()
camera.close()
