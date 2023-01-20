import time

from scicamera import Camera

camera = Camera()
camera.start_runloop()
camera.start()
camera.discard_frames(2).result()
camera.stop_runloop()

time.sleep(1)

camera.start_runloop()
camera.discard_frames(2).result()
camera.stop()
camera.stop_runloop()


camera.close()
