import libcamera

from scicamera import Camera, CameraConfig


def test_transform(camera: Camera):
    camera.start_preview()

    preview_config = CameraConfig.for_preview(camera)
    preview_config.transform = libcamera.Transform(hflip=1, vflip=1)
    camera.configure(preview_config)

    camera.start()
    camera.discard_frames(2).result()
    camera.stop()
