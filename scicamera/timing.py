from logging import getLogger

import numpy as np

from scicamera.camera import Camera
from scicamera.request import CompletedRequest

_log = getLogger(__name__)


def calibrate_camera_offset(camera: Camera, n_frames: int = 100) -> int:
    """Calibrate the ``SensorTimestamp`` wrt to the epoch time.

    Returns the number of integer nanoseconds you should add to
    the camera ``SensorTimestamp`` to get the epoch time in nanoseconds.
    """
    deltas = []

    def _capture_dt_callback(request: CompletedRequest):
        # This is the time the request was handed to python
        # Note casting takes place to minimize precision loss to float32 math
        epoch_nanos = int(request.completion_time * 1000000) * 1000
        sensor_nanos = request.get_metadata()["SensorTimestamp"]
        deltas.append(epoch_nanos - sensor_nanos)

    camera.add_request_callback(_capture_dt_callback)
    camera.discard_frames(n_frames).result()
    camera.remove_request_callback(_capture_dt_callback)

    deltas = np.array(deltas, dtype=np.int64)
    offset = np.mean(deltas, dtype=np.uint64)
    stdev = np.std(deltas, dtype=np.uint64)

    _log.warning(f"Camera offset: {offset} +/-{stdev}")
    return offset.item()
