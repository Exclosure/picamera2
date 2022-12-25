from logging import getLogger

from picamera2 import Picamera2

_log = getLogger(__name__)
_log.info("Preview re-initialized after start.")
picam2 = Picamera2()
preview = picam2.create_preview_configuration()
picam2.configure(preview)
picam2.start()
np_array = picam2.capture_array()
_log.info(np_array)
picam2.close()
