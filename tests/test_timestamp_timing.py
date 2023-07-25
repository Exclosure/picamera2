import time
from typing import Type

import numpy as np
import pytest

from scicamera import Camera, CameraConfig
from scicamera.fake import FakeCamera


@pytest.mark.parametrize("CameraClass", [Camera, FakeCamera])
def test_timestamps(CameraClass: Type[Camera]):
    with CameraClass() as camera:
        video_config = CameraConfig.for_video(camera)
        camera.configure(video_config)

        timestamps = []

        def _callback(request):
            timestamps.append(time.time() * 1e6)
            if len(timestamps) == 10:
                camera.remove_request_callback(_callback)

        camera.add_request_callback(_callback)

        camera.start()
        camera.discard_frames(10).result(timeout=5.0)
        camera.stop()

    # Now let's analyse all the timestamps
    timestamps = np.array(timestamps)
    diffs = timestamps[1:] - timestamps[:-1]
    median = np.median(diffs)
    tol = median / 5
    print(diffs)
    hist, _ = np.histogram(
        diffs,
        bins=[
            0,
            median - tol,
            median + tol,
            2 * median + tol,
            max(3 * median, diffs.max()),
        ],
    )
    print("[Early, expected, late, very late] =", hist)

    if abs(median - 33333) > tol:
        raise RuntimeError(f"Frame intervals are {median}us but should be 33333us")
    if hist[0] > 0:
        raise RuntimeError(f"{hist[0]} frame times less than the expected interval")
    if hist[2] > 3:
        raise RuntimeError(f"Unexpectedly large number ({hist[2]}) of late frames")
    if hist[3] > 0:
        raise RuntimeError(f"{hist[3]} very late frames detected")
