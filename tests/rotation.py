#!/usr/bin/python3

# Run the camera with a 180 degree rotation.
import sys

sys.path.append("/usr/lib/python3/dist-packages")
import libcamera

from picamera2 import Picamera2, CameraConfiguration

camera = Picamera2()
camera.start_preview()

preview_config = CameraConfiguration.create_preview_configuration(camera)
preview_config.transform = libcamera.Transform(hflip=1, vflip=1)
camera.configure(preview_config)

camera.start()
camera.discard_frames(2).result()
camera.stop()
