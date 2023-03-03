from scicamera import Camera
from scicamera.testing import mature_after_frames_or_timeout

camera = Camera()
try:
    mature_after_frames_or_timeout(camera)
except TimeoutError:
    print("Timed out! (expected)")

camera.start()

mature_after_frames_or_timeout(camera)
