#!/usr/bin/python3
from unittest.mock import MagicMock

from picamera2 import Picamera2
from picamera2.testing import mature_after_frames_or_timeout

camera = Picamera2()
fps = 30
dur = 5

micro = int((1 / fps) * 1000000)
video_cfg = camera.create_video_configuration()
video_cfg["controls"]["FrameDurationLimits"] = (micro, micro)

camera.configure(video_cfg)

mock = MagicMock()
camera.add_request_callback(lambda r: mock())

with camera:
    mature_after_frames_or_timeout(camera, 5).result()
