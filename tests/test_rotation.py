import libcamera

from scicamera import Camera, CameraConfig

# Run the camera with a 180 degree rotation.

def test_rotation():
    with Camera() as camera:
        camera.start_runloop()

        preview_config = CameraConfig.for_preview(camera)
        preview_config.transform = libcamera.Transform(hflip=1, vflip=1)
        camera.configure(preview_config)

        camera.start()
        camera.discard_frames(2).result()
        camera.stop()
