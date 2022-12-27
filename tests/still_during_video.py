#!/usr/bin/python3
from picamera2 import Picamera2

# Encode a VGA stream, and capture a higher resolution still image half way through.

camera = Picamera2()
half_resolution = [dim // 2 for dim in camera.sensor_resolution]
main_stream = {"size": half_resolution}
lores_stream = {"size": (640, 480)}
video_config = camera.create_video_configuration(main_stream, lores_stream)
camera.configure(video_config)

# It's better to capture the still in this thread, not in the one driving the camera.
request = camera.capture_request()
request.save("main", "test.jpg")
request.release()
print("Still image captured!")
