#!/usr/bin/python3
from scicamera import Camera, CameraConfig


def test_capture_video_timestamp(camera: Camera):
    video_config = CameraConfig.for_video(camera)
    camera.configure(video_config)

    camera.start()
    camera.discard_frames(2).result()
