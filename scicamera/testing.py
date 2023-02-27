from __future__ import annotations

import sys
from concurrent.futures import Future
from typing import Iterable, NoReturn
from unittest.mock import Mock

from scicamera import Camera
from scicamera.request import CompletedRequest


def elapse_frames_or_timeout(camera: Camera, n_frames: int, timeout_seconds=5):
    """Wait for ``camera`` to complete ``n_frames`` frames, or timeout.

    If the frames are not produces within ``timeout_seconds`` a ``TimeoutError``
    will be raised."""
    future = Future()
    future.set_running_or_notify_cancel()
    mock = Mock()

    def callback(request: CompletedRequest):
        mock(request)
        if mock.call_count == n_frames:
            future.set_result(None)

    camera.add_request_callback(callback)

    try:
        future.result(timeout=timeout_seconds)
    finally:
        camera.remove_request_callback(callback)


def _skip_hack(message: str) -> NoReturn:
    try:
        import pytest

        pytest.skip(reason=message)
    except ImportError:
        print(message, file=sys.stderr)
        sys.exit(0)


def requires_controls(camera: Camera, controls: Iterable[str]) -> None | NoReturn:
    """Decorator to skip tests if the camera does not support the given controls."""
    # NOTE(meawoppl) - This should be a pytest.skip(), but because of the way
    # tests are run in subprocesses, pytest.skip() doesn't work... TODO FIXME

    available_controls = camera.controls.available_control_names()
    missing_controls = set(controls) - available_controls

    if not missing_controls:
        return

    camera.close()
    _skip_hack(f"Skipping test, missing controls: {missing_controls}")


def requires_non_mjpeg(camera: Camera):
    if camera.sensor_format == "MJPEG":
        camera.close()
        _skip_hack("Skipping test, MJPEG only camera: {camera}")
