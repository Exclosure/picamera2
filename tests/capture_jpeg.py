#!/usr/bin/python3
# Capture a JPEG while still running in the preview mode. When you
# capture to a file, the return value is the metadata for that image.

from scicamera import Camera, CameraConfig

camera = Camera()

preview_config = CameraConfig.for_preview(camera, main={"size": (800, 600)})
camera.configure(preview_config)

camera.start_runloop()

camera.start()
camera.discard_frames(2)
metadata = camera.capture_file("test.jpg").result()
print(metadata)

camera.close()
