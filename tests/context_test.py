import time

from picamera2 import Picamera2, CameraConfiguration


def main():
    print("With context...")
    with Picamera2() as camera:
        config = CameraConfiguration.create_preview_configuration(camera)
        camera.configure(config)
        camera.start()
        metadata = camera.capture_metadata().result()
        assert isinstance(metadata, dict)
        print(metadata)

    print("Without context...")
    camera = Picamera2()
    config = CameraConfiguration.create_preview_configuration(camera)
    camera.configure(config)
    camera.start()
    metadata = camera.capture_metadata().result()
    print(metadata)
    camera.stop_preview()
    camera.close()


if __name__ == "__main__":
    main()
