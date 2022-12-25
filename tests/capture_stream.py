#!/usr/bin/python3

import socket
import time

from picamera2 import Picamera2
from picamera2.encoders.jpeg_encoder import JpegEncoder
from picamera2.outputs import FileOutput

camera = Picamera2()
video_config = camera.create_video_configuration({"size": (1280, 720)})
camera.configure(video_config)
encoder = JpegEncoder()

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("0.0.0.0", 10001))
    sock.listen()

    camera.encoder = encoder

    conn, addr = sock.accept()
    stream = conn.makefile("wb")
    camera.encoder.output = FileOutput(stream)
    camera.start_encoder()
    camera.start()
    time.sleep(2)
    camera.stop()
    camera.stop_encoder()
    conn.close()

camera.close()
