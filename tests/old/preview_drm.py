#!/usr/bin/python3

# For use from the login console, when not running X Windows.
from scicamera import Camera, CameraConfig

with Camera() as camera:
    camera.start_runloop()

    preview_config = CameraConfig.for_preview(camera, {"size": (640, 360)})
    camera.configure(preview_config)

    camera.start()
    camera.discard_frames(2).result()
    camera.stop()
