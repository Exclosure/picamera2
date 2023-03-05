from __future__ import annotations

from dataclasses import dataclass
from logging import getLogger
from typing import List

import libcamera

_log = getLogger(__name__)


@dataclass
class CameraInfo:
    id: str
    """Unique identifier for this camera."""

    model: str
    """Model name for this camera."""

    location: str | None
    """Location of the camera, if known."""

    rotation: int | None
    """Rotation of the camera, if known."""

    @staticmethod
    def global_camera_info() -> List[CameraInfo]:
        """
        Return Id string and Model name for all attached cameras, one dict per camera,
        and ordered correctly by camera number. Also return the location and rotation
        of the camera when known, as these may help distinguish which is which.
        """
        infos = []
        for cam in libcamera.CameraManager.singleton().cameras:
            name_to_val = {}
            for k, v in cam.properties.items():
                if k.name in ("Model", "Location", "Rotation"):
                    name_to_val[k.name.lower()] = v
                else:
                    _log.warning("Unknown property %s: %s", k.name, v)
            name_to_val["id"] = cam.id
            infos.append(CameraInfo(**name_to_val))
        return infos

    @staticmethod
    def n_cameras() -> int:
        """Return the number of attached cameras."""
        return len(libcamera.CameraManager.singleton().cameras)

    def requires_camera(needed: int = 1) -> None:
        """Require a minimum number of cameras to be attached.

        Raises: RuntimeError if not enough cameras are found.
        """
        found = CameraInfo.n_cameras()
        if found < needed:
            msg = "{n} camera(s) required found {found} not found (need) (Do not forget to disable legacy camera with raspi-config)."
            _log.error(msg)
            raise RuntimeError(msg)
