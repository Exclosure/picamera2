#!/usr/bin/python3
from picamera2 import CameraConfiguration, Picamera2
from picamera2.testing import mature_after_frames_or_timeout

camera = Picamera2()
fps = 30
dur = 5

micro = int((1 / fps) * 1000000)
video_cfg = CameraConfiguration.create_video_configuration(camera)
video_cfg.controls.FrameDurationLimits = (micro, micro)
camera.configure(video_cfg)

camera.start()
mature_after_frames_or_timeout(camera, 5).result()
camera.stop()
camera.close()
