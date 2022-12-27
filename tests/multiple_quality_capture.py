#!/usr/bin/python3
import time

from picamera2 import Picamera2

camera = Picamera2()
video_config = camera.create_video_configuration()
camera.configure(video_config)

camera.start()
camera.discard_frames(4)
camera.stop()
camera.close()
