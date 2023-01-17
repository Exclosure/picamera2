#!/usr/bin/python3

# The QtPreview uses software rendering and thus makes more use of the
# CPU, but it does work with X forwarding, unlike the QtGlPreview.

from scicamera import CameraConfig, Camera

camera = Camera()
camera.start_preview()

preview_config = CameraConfig.for_preview(camera)
camera.configure(preview_config)

camera.start()
camera.discard_frames(2).result()
camera.stop()

camera.close()
