#!/usr/bin/python3
import numpy as np

from picamera2 import Picamera2, CameraConfiguration

lsize = (320, 240)
camera = Picamera2()
video_config = CameraConfiguration.create_video_configuration(
    camera,
    main={"size": (1280, 720), "format": "RGB888"},
    lores={"size": lsize, "format": "YUV420"},
)
camera.configure(video_config)

camera.start()

w, h = lsize
prev = None
encoding = False
ltime = 0

for _ in range(4):
    cur = camera.capture_buffer("lores").result()
    cur = cur[: w * h].reshape(h, w)
    if prev is not None:
        # Measure pixels differences between current and
        # previous frame
        mse = np.square(np.subtract(cur, prev)).mean()
        print(mse)
    prev = cur
