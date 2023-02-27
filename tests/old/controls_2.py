from scicamera import Camera, CameraConfig
from scicamera.testing import requires_controls


def test_set_aec_agc(camera: Camera):
    requires_controls(camera, {"AwbEnable", "AeEnable"})
    camera.start_preview()

    preview_config = CameraConfig.for_preview(camera)
    camera.configure(preview_config)

    camera.start()
    camera.discard_frames(2)

    camera.set_controls({"AwbEnable": 0, "AeEnable": 0})
    camera.discard_frames(2).result()
    camera.close()
