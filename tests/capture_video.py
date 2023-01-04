#!/usr/bin/python3
from picamera2 import CameraConfiguration, Picamera2

camera = Picamera2()
video_config = CameraConfiguration.create_video_configuration(camera)
camera.configure(video_config)

camera.start()
camera.discard_frames(2).result()
camera.stop()
camera.close()
