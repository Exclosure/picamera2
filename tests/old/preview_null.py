#!/usr/bin/python3

from scicamera import Camera, CameraConfig


def test_minimal(camera: Camera):
    config = CameraConfig.for_preview(camera)
    camera.configure(config)

    camera.start()
    camera.discard_frames(4).result()
    camera.stop()
