import re
import sys
from concurrent.futures._base import TimeoutError as FuturesTimeoutError
from typing import Iterable
import logging
import pytest

from scicamera import Camera, FakeCamera

_log = logging.getLogger(__name__)

def mature_after_frames_or_timeout(
    camera: Camera, n_frames: int = 2, timeout_seconds=5
):
    """Return a future that will be mature after n_frames or 2 seconds.

    Raises: TimeoutError if it takes too long.
    """
    try:
        camera.discard_frames(n_frames).result(timeout_seconds)
    except FuturesTimeoutError as e:
        raise TimeoutError("Timed out waiting for camera to mature") from e


def requires_camera_model(camera: Camera, model_pattern: str, allow_fake: bool = True):
    if isinstance(camera, FakeCamera) and allow_fake:
        return
    model_name = camera.info.model
    if not re.match(model_pattern, model_name):
        _log.warning("Closing camera in fixture.")
        camera.close()
        pytest.skip(
            f"Skipping test, camera model {model_name} does not match {model_pattern}"
        )


def requires_controls(camera: Camera, controls: Iterable[str]):
    """Decorator to skip tests if the camera does not support the given controls."""
    # NOTE(meawoppl) - This should be a pytest.skip(), but because of the way
    # tests are run in subprocesses, pytest.skip() doesn't work... TODO FIXME

    available_controls = camera.controls.available_control_names()
    missing_controls = set(controls) - available_controls

    if missing_controls:
        print("Skipping test, missing controls:", missing_controls)
        sys.exit(0)
