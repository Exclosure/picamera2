#!/usr/bin/python3

# Switch from preview to full resolution mode (alternative method).
from picamera2 import Picamera2, CameraConfiguration

camera = Picamera2()
camera.start_preview()

preview_config = CameraConfiguration.create_preview_configuration(camera)
camera.configure(preview_config)

camera.start()
camera.discard_frames(4)
camera.stop()

other_config = CameraConfiguration.create_preview_configuration(
    camera,
    main={"size": camera.sensor_resolution}, buffer_count=3
)
camera.configure(other_config)

camera.start()
camera.discard_frames(4).result()
camera.stop()
camera.close()
