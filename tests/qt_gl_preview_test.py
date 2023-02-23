from scicamera import Camera, CameraConfig


def test_camera_reinit():
    for i in range(2):
        print(f"{i} preview...")
        camera = Camera()
        camera.configure(CameraConfig.for_preview(camera))
        camera.start_preview()
        camera.start()
        camera.discard_frames(5).result()
        camera.close()
        print("Done")
