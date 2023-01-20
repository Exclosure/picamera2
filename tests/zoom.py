#!/usr/bin/python3

# How to do digital zoom using the "ScalerCrop" control.

from scicamera import Camera, CameraConfig

camera = Camera()
camera.start_runloop()

preview_config = CameraConfig.for_preview(camera)
camera.configure(preview_config)

camera.start()

size = camera.capture_metadata().result()["ScalerCrop"][2:]

for _ in range(20):
    # This syncs us to the arrival of a new camera frame:
    camera.capture_metadata()

    size = [int(s * 0.95) for s in size]
    offset = [(r - s) // 2 for r, s in zip(camera.sensor_resolution, size)]
    camera.set_controls({"ScalerCrop": offset + size})

camera.stop()
camera.close()
