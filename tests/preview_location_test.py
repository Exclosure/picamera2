from logging import getLogger
import time

from picamera2 import Picamera2, Preview

_log = getLogger(__name__)
_log.info("Preview re-initialized after start.")
picam2 = Picamera2()
preview = picam2.create_preview_configuration()
picam2.configure(preview)
picam2.start_preview(Preview.NULL)
picam2.start()
np_array = picam2.capture_array()
_log.info(np_array)
time.sleep(5)
picam2.stop_preview()
picam2.close()
