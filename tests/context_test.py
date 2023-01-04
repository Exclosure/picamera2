import time

from picamera2 import CameraConfig, Picamera2


def main():
    print("With context...")
    with Picamera2() as camera:
        config = CameraConfig.create_preview_configuration(camera)
        camera.configure(config)
        camera.start()
        metadata = camera.capture_metadata().result()
        assert isinstance(metadata, dict)
        print(metadata)

    print("Without context...")
    camera = Picamera2()
    config = CameraConfig.create_preview_configuration(camera)
    camera.configure(config)
    camera.start()
    metadata = camera.capture_metadata().result()
    print(metadata)
    camera.stop_preview()
    camera.close()


if __name__ == "__main__":
    main()
