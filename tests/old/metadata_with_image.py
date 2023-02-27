from scicamera import Camera, CameraConfig


def test_get_image_and_meta(camera: Camera):
    camera.start_preview()

    preview_config = CameraConfig.for_preview(camera)
    camera.configure(preview_config)

    camera.start()
    camera.discard_frames(2)

    request = camera.capture_request().result()
    request.make_image("main")  # image from the "main" stream
    metadata = request.get_metadata()
    request.release()  # requests must always be returned to libcamera

    print(metadata)
