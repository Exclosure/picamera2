from scicamera import Camera, CameraConfig


def test_minimal(camera: Camera):
    camera.start_preview()

    preview_config = CameraConfig.for_preview(camera)
    camera.configure(preview_config)

    camera.start()
    camera.discard_frames(2).result()
    camera.stop()
