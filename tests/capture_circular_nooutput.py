#!/usr/bin/python3
import sys
import time

from picamera2 import Picamera2
from picamera2.encoders import MJPEGEncoder
from picamera2.outputs import CircularOutput

picam2 = Picamera2()
fps = 30
dur = 5
micro = int((1 / fps) * 1000000)
vconfig = picam2.create_video_configuration()
vconfig["controls"]["FrameDurationLimits"] = (micro, micro)
picam2.configure(vconfig)
encoder = MJPEGEncoder()
output = CircularOutput(buffersize=int(fps * (dur + 0.2)), outputtofile=False)
output.fileoutput = "file.mjpeg"
picam2.start_recording(encoder, output)
time.sleep(dur)
output.stop()
