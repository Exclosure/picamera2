#!/usr/bin/python3
# Use the configuration structure method to do a full res capture.
from scicamera import Camera, CameraConfig
from scicamera.testing import mature_after_frames_or_timeout

with Camera() as camera:
    # We don't really need to change anything, but let's mess around just as a test.
    preview_config = CameraConfig.for_preview(camera)
    preview_config.main.size = (800, 600)
    preview_config.main.format = "YUV420"

    still_config = CameraConfig.for_still(camera)
    still_config.main.size = (1600, 1200)
    still_config.enable_raw()
    still_config.raw.size = camera.sensor_resolution

    camera.configure(preview_config)
    camera.start()
    mature_after_frames_or_timeout(camera)
    assert camera.capture_image(config=still_config).result()
    camera.stop()
