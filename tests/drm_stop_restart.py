import time

from scicamera import Camera

camera = Camera()

for _ in range(3):
    camera.start()
    camera.discard_frames(2).result()
    camera.stop()

camera.close()
