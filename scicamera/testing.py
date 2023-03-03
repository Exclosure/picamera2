import sys
from typing import Iterable

from scicamera import Camera


def mature_after_frames_or_timeout(camera: Camera, n_frames: int=2, timeout_seconds=5):
    """Return a future that will be mature after n_frames or 2 seconds.

    Raises: TimeoutError if it takes too long.
    """
    camera.discard_frames(n_frames).result(timeout_seconds)


def requires_controls(camera: Camera, controls: Iterable[str]):
    """Decorator to skip tests if the camera does not support the given controls."""
    # NOTE(meawoppl) - This should be a pytest.skip(), but because of the way
    # tests are run in subprocesses, pytest.skip() doesn't work... TODO FIXME

    available_controls = camera.controls.available_control_names()
    missing_controls = set(controls) - available_controls

    if missing_controls:
        print("Skipping test, missing controls:", missing_controls)
        sys.exit(0)
