#!/usr/bin/python3
# Start camera with fixed exposure and gain.
from picamera2 import CameraConfiguration, Picamera2

camera = Picamera2()
camera.start_preview()
controls = {"ExposureTime": 10000, "AnalogueGain": 1.0}
preview_config = CameraConfiguration.create_preview_configuration(
    camera, controls=controls
)
camera.configure(preview_config)

camera.start()
camera.discard_frames(2).result()
camera.close()
