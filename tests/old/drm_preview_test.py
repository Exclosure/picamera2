from scicamera import Camera, CameraConfig


def test_preview_config(camera: Camera):
    print("First preview...")
    camera = Camera()
    camera.configure(CameraConfig.for_preview(camera))
    camera.start_preview()
    camera.start()
    camera.discard_frames(2).result()
    camera.close()
    print("Done")

    print("Second preview...")
    camera = Camera()
    camera.configure(CameraConfig.for_preview(camera))
    camera.start_preview()
    camera.start()
    camera.discard_frames(2).result()
    camera.close()
    print("Done")
