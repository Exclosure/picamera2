#!/usr/bin/python3
import numpy as np

from picamera2 import CameraConfiguration, Picamera2

lsize = (320, 240)
camera = Picamera2()
video_config = CameraConfiguration.create_video_configuration(
    camera,
    main={"size": (1280, 720), "format": "RGB888"},
    lores={"size": lsize, "format": "YUV420"},
)
camera.configure(video_config)
camera.start_preview()
camera.start()
camera.discard_frames(10)

w, h = lsize
prev = None
ltime = 0

for _ in range(4):
    cur = camera.capture_array("lores").result()
    if prev is not None:
        # Measure pixels differences between current and
        # previous frame
        mse = np.square(np.subtract(cur, prev)).mean()
        print("New Motion", mse)
    prev = cur

camera.close()
