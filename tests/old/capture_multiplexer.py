#!/usr/bin/python3
from scicamera import Camera, CameraConfig


def takephoto(cam):
    camera = Camera(camera_num=cam)
    capture_config = CameraConfig.for_still(camera)
    camera.start()
    camera.capture_file(f"cam{cam}.jpg", config=capture_config).result()
    camera.stop()
    camera.close()


for cam in range(4):
    takephoto(cam)

# Or
for cam in range(4):
    camera = Camera(camera_num=cam)
    capture_config = CameraConfig.for_still(camera)
    camera.start()
    camera.capture_file(f"cam{cam}.jpg", config=capture_config).result()
    camera.stop()
    camera.close()
