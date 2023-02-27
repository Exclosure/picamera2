#!/usr/bin/python3

# Test that we can successfully close a QtGlPreview window and open a new one.

from scicamera import Camera, CameraConfig

print("First preview...")
camera = Camera()
camera.configure(CameraConfig.for_preview(camera))
camera.start_runloop()
camera.start()
camera.discard_frames(2).result()
camera.close()
print("Done")

print("Second preview...")
camera = Camera()
camera.configure(CameraConfig.for_preview(camera))
camera.start_runloop()
camera.start()
camera.discard_frames(2).result()
camera.close()
print("Done")
