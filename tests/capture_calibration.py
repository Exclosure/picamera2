#!/usr/bin/python3
from datetime import datetime, timezone

from scicamera import Camera, CameraConfig
from scicamera.timing import calibrate_camera_offset

camera = Camera()
video_config = CameraConfig.for_video(camera)
camera.configure(video_config)

camera.start()
offset = calibrate_camera_offset(camera, 20)

ts = camera.capture_metadata().result()["SensorTimestamp"]
exposure_time = datetime.fromtimestamp((ts + offset) / 1e9)
assert abs(exposure_time - datetime.now()).total_seconds() < 1

camera.stop()
camera.close()
