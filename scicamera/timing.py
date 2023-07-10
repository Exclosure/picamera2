import math
from logging import getLogger

from scicamera.camera import Camera
from scicamera.request import CompletedRequest

_log = getLogger(__name__)


def calibrate_camera_offset(
    camera: Camera,
    n_frames: int = 100,
) -> float:
    """Calibrate the ``SensorTimestamp`` wrt to the epoch time.

    Returns the number of nanoseconds you should add to the camera
    ``SensorTimestamp`` to get the epoch time in nanoseconds.
    """
    deltas = []

    def _capture_timing_callback(request: CompletedRequest):
        # This is the time the request was handed to python
        epoch_nanos = int(request.completion_time * 1_000_000_000)
        # This is the time the "sensor" reports `ktime_get_ns()` in the kernel
        sensor_nanos = request.get_metadata()["SensorTimestamp"]
        deltas.append(epoch_nanos - sensor_nanos)

    # Make sure the above callback happens at least `n_frames` times
    camera.add_request_callback(_capture_timing_callback)
    camera.discard_frames(n_frames).result()
    camera.remove_request_callback(_capture_timing_callback)

    # NB: This segment relies on python's integer size growth
    offset = sum(deltas) / len(deltas)
    diffs = sum([(d - offset) ** 2 for d in deltas])
    stdev = math.sqrt(diffs / (len(deltas) - 1))

    _log.warning(f"Camera offset: {offset} ± {stdev}")
    return offset
