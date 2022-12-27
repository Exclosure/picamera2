#!/usr/bin/python3
import time
from unittest.mock import MagicMock

from picamera2 import Picamera2
from picamera2.encoders.jpeg_encoder import JpegEncoder
from picamera2.outputs import CircularOutput

camera = Picamera2()
fps = 30
dur = 5

micro = int((1 / fps) * 1000000)
vconfig = camera.create_video_configuration()
vconfig["controls"]["FrameDurationLimits"] = (micro, micro)

camera.configure(vconfig)
encoder = JpegEncoder()
output = CircularOutput(buffersize=int(fps * (dur + 0.2)), outputtofile=False)
output.fileoutput = "file.mjpeg"

mock = MagicMock()
camera.add_request_callback(lambda r: mock())

start_time = time.time()
while (mock.call_count < 5) and (time.time() - start_time < 5):
    time.sleep(0.1)

output.stop()

camera.close()

assert mock.call_count > 0