#!/usr/bin/python3
from scicamera import Camera, CameraConfig
from scicamera.testing import elapse_frames_or_timeout, requires_controls


def test_video_configuration(camera: Camera):
    requires_controls(camera, ("FrameDurationLimits",))

    video_cfg = CameraConfig.for_video(camera)
    fps = 30
    micro = int((1 / fps) * 1000000)
    video_cfg.controls.FrameDurationLimits = (micro, micro)

    camera.configure(video_cfg)

    camera.start()
    elapse_frames_or_timeout(camera, 5)
    camera.stop()
    camera.close()
