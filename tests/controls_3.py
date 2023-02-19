#!/usr/bin/python3
# Example of setting controls using the "direct" attribute method.
from scicamera import Camera, CameraConfig
from scicamera.controls import Controls

camera = Camera()
camera.start_preview()

preview_config = CameraConfig.for_preview(camera)
camera.configure(preview_config)

camera.start()
camera.discard_frames(2)

controls = Controls(camera)
if "AnalogueGain" in controls.available_control_names():
    controls.AnalogueGain = 1.0
if "ExposureTime" in controls.available_control_names():
    controls.ExposureTime = 10000

camera.set_controls(controls)
camera.discard_frames(2).result()
camera.close()
