from __future__ import annotations

from dataclasses import dataclass
from logging import getLogger
from typing import List

import libcamera

from scicamera.lc_helpers import lc_unpack

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

    size: tuple[int, int] | None
    """Size of the pixel array, if known."""

    @staticmethod
    def global_camera_info() -> List[CameraInfo]:
        """
        Return Id string and Model name for all attached cameras, one dict per camera,
        and ordered correctly by camera number. Also return the location and rotation
        of the camera when known, as these may help distinguish which is which.
        """
        return list(
            CameraInfo.from_lc_camera(cam)
            for cam in libcamera.CameraManager.singleton().cameras
        )

    @classmethod
    def from_lc_camera(cls, lc_camera: libcamera.Camera) -> CameraInfo:
        name_to_val = {"location": None, "rotation": None, "size": None, "model": None}
        _log.debug("Camera Property Keys: %s", lc_unpack(lc_camera.properties))
        for k, v in lc_camera.properties.items():
            renamed = k.name.lower()
            if renamed == "pixelarraysize":
                renamed = "size"
            if renamed in name_to_val:
                name_to_val[renamed] = v
            else:
                _log.debug("Unknown property %s: %s", k.name, v)
        name_to_val["id"] = lc_camera.id
        return cls(**name_to_val)

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
            msg = (
                f"{needed} camera(s) required, but only found {found}"
                f"(Do not forget to disable legacy camera with raspi-config)."
            )
            _log.error(msg)
            raise RuntimeError(msg)
