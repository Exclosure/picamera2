import importlib.metadata

import libcamera

from scicamera.camera import Camera, CameraManager
from scicamera.configuration import CameraConfig, StreamConfig
from scicamera.controls import Controls
from scicamera.fake import FakeCamera
from scicamera.info import CameraInfo
from scicamera.lc_helpers import libcamera_color_spaces_eq, libcamera_transforms_eq

# NOTE(meawoppl) - ugleeee monkey patch. Kill the below VV
libcamera.Transform.__repr__ = libcamera.Transform.__str__
libcamera.Transform.__eq__ = libcamera_transforms_eq

libcamera.ColorSpace.__repr__ = libcamera.ColorSpace.__str__
libcamera.ColorSpace.__eq__ = libcamera_color_spaces_eq


__all__ = [
    "Camera",
    "CameraConfig",
    "CameraInfo",
    "CameraManager",
    "CompletedRequest",
    "Controls",
    "FakeCamera",
    "StreamConfig",
]

try:
    __version__ = importlib.metadata.version(__package__ or __name__)
except ModuleNotFoundError:
    __version__ = "0.0.0-localdev"
