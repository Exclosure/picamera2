import time
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
        epoch_nanos = int(request.completion_time * 1_000_000_000)
        sensor_nanos = request.get_metadata()["SensorTimestamp"]
        delta = epoch_nanos - sensor_nanos
        print(f"Epoch Nanos: {epoch_nanos} ({len(str(epoch_nanos))}) Sensor Nanos: {sensor_nanos}({len(str(sensor_nanos))}) Delta: {delta}")
        deltas.append(delta)

    camera.add_request_callback(_capture_dt_callback)
    camera.discard_frames(n_frames).result()
    camera.remove_request_callback(_capture_dt_callback)

    print(deltas)
    deltas = np.array(deltas, dtype=np.float256)
    print(deltas)
    offset = np.mean(deltas, dtype=np.float256)
    stdev = np.std(deltas, dtype=np.float256)

    _log.warning(f"Camera offset: {offset} +/-{stdev}")
    return offset.item()
