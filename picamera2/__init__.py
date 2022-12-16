import sys

sys.path.append("/usr/lib/python3/dist-packages")
import libcamera

from picamera2.configuration import CameraConfiguration, StreamConfiguration
from picamera2.controls import Controls
from picamera2.converters import YUV420_to_RGB
from picamera2.metadata import Metadata
from picamera2.picamera2 import Picamera2, Preview
from picamera2.request import CompletedRequest, MappedArray

# TODO(meawoppl) - Make Transforms dataclasses and percolate out
# the logic below into them
def libcamera_transforms_eq(t1, t2):
    return (
        t1.hflip == t2.hflip and t1.vflip == t2.vflip and t1.transpose == t2.transpose
    )


def libcamera_colour_spaces_eq(c1, c2):
    return (
        c1.primaries == c2.primaries
        and c1.transferFunction == c2.transferFunction
        and c1.ycbcrEncoding == c2.ycbcrEncoding
        and c1.range == c2.range
    )

# NOTE(meawoppl) - ugleeee monkey patch. Kill the below VV
libcamera.Transform.__repr__ = libcamera.Transform.__str__
libcamera.Transform.__eq__ = libcamera_transforms_eq

libcamera.ColorSpace.__repr__ = libcamera.ColorSpace.__str__
libcamera.ColorSpace.__eq__ = libcamera_colour_spaces_eq
