#!/usr/bin/python3
from datetime import datetime, timezone

from scicamera import Camera, CameraConfig
from scicamera.timing import calibrate_camera_offset

camera = Camera()
video_config = CameraConfig.for_video(camera)
camera.configure(video_config)

camera.start()
offset = calibrate_camera_offset(camera, 20)

sensor_timestamp = camera.capture_metadata().result()["SensorTimestamp"]
print("Timestamp: ", sensor_timestamp)
print("Offset: ", offset)
exposure_time = datetime.fromtimestamp((sensor_timestamp + offset) / 1e9)
time_offset = abs(exposure_time - datetime.now()).total_seconds()

assert time_offset < 1, time_offset

camera.stop()
camera.close()
