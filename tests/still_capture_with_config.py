# Use the configuration structure method to do a full res capture.
from scicamera import Camera
from scicamera.testing import elapse_frames_or_timeout, requires_non_mjpeg


def test_still_with_config(camera: Camera):
    requires_non_mjpeg(camera)

    # We don't really need to change anything, but let's mess around just as a test.
    camera.preview_configuration.size = (800, 600)
    camera.preview_configuration.format = "YUV420"

    camera.still_configuration.size = (1600, 1200)
    camera.still_configuration.enable_raw()
    camera.still_configuration.raw.size = camera.sensor_resolution

    camera.start("preview")
    elapse_frames_or_timeout(camera, 3)
    assert camera.capture_image(config="still").result()
    camera.stop()
