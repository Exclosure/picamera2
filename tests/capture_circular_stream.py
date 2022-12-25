#!/usr/bin/python3
import socket
import threading
import time

import numpy as np

from picamera2 import Picamera2
from picamera2.encoders.jpeg_encoder import JpegEncoder
from picamera2.outputs import CircularOutput, FileOutput

lsize = (320, 240)
camera = Picamera2()
video_config = camera.create_video_configuration(
    main={"size": (1280, 720), "format": "RGB888"},
    lores={"size": lsize, "format": "YUV420"},
)
camera.configure(video_config)
camera.start_preview()
encoder = JpegEncoder()
circ = CircularOutput()
encoder.output = [circ]
camera.encoder = encoder
camera.start()
camera.start_encoder()

w, h = lsize
prev = None
encoding = False
ltime = 0


def server():
    global circ, camera
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("0.0.0.0", 10001))
        sock.listen()
        while tup := sock.accept():
            event = threading.Event()
            conn, addr = tup
            stream = conn.makefile("wb")
            filestream = FileOutput(stream)
            filestream.start()
            camera.encoder.output = [circ, filestream]
            filestream.connectiondead = lambda ex: event.set()
            event.wait()


t = threading.Thread(target=server)
t.setDaemon(True)
t.start()

while True:
    cur = camera.capture_buffer("lores")
    cur = cur[: w * h].reshape(h, w)
    if prev is not None:
        # Measure pixels differences between current and
        # previous frame
        mse = np.square(np.subtract(cur, prev)).mean()
        if mse > 7:
            if not encoding:
                epoch = int(time.time())
                circ.fileoutput = "{}.mjpeg".format(epoch)
                circ.start()
                encoding = True
                print("New Motion", mse)
            ltime = time.time()
        else:
            if encoding and time.time() - ltime > 5.0:
                circ.stop()
                encoding = False
    prev = cur

camera.stop_encoder()
