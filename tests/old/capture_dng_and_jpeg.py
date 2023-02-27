#!/usr/bin/python3
# Capture a DNG and a JPEG made from the same raw data.
from scicamera import Camera
from scicamera.configuration import CameraConfig


def test_capture_dng_and_jpeg(camera: Camera):
    camera.start_preview()
    camera.configure("preview")

    camera.start()
    camera.discard_frames(2)

    capture_config = CameraConfig.for_still(camera)
    camera.switch_mode(capture_config).result()
    request = camera.capture_request(capture_config).result()
    request.make_image("main").convert("RGB").save("full.jpg")
    request.release()
