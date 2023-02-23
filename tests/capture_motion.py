#!/usr/bin/python3
import numpy as np

from scicamera import Camera, CameraConfig


def test_capture_motion(camera: Camera):
    lsize = w, h = (320, 240)
    video_config = CameraConfig.for_video(
        camera,
        main={"size": (1280, 720), "format": "RGB888"},
        lores={"size": lsize, "format": "YUV420"},
    )
    camera.configure(video_config)

    camera.start()

    prev = None

    for _ in range(4):
        cur = camera.capture_buffer("lores").result()
        cur = cur[: w * h].reshape(h, w)
        if prev is not None:
            # Measure pixels differences between current and
            # previous frame
            mse = np.square(np.subtract(cur, prev)).mean()
            print(mse)
        prev = cur
