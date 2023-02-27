#!/usr/bin/python3
from scicamera import Camera, CameraConfig
from scicamera.testing import elapse_frames_or_timeout


def test_capture_mjpeg(camera: Camera):
    video_config = CameraConfig.for_video(camera, main={"size": (1920, 1080)})
    camera.configure(video_config)

    camera.start_preview()

    camera.start()
    elapse_frames_or_timeout(camera, 5)
