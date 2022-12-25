import time
from logging import getLogger

from picamera2 import Picamera2, Preview

wait = 2
buffer = 1

_log = getLogger(__name__)


def main():
    # First we create a camera instance.
    picam2 = Picamera2()

    # Let's set it up for previewing.
    preview = picam2.create_preview_configuration()
    picam2.configure(preview)

    picam2.start(show_preview=None)

    null1 = time.monotonic()
    print("Null Preview")
    time.sleep(buffer)
    picam2.start_preview(Preview.NULL)
    time.sleep(wait)
    picam2.stop_preview()
    null2 = time.monotonic()

    # Close the camera.
    picam2.close()

    _log.info(f"Null Cycle Results: {null2-null1-wait-buffer} s")


if __name__ == "__main__":
    main()
