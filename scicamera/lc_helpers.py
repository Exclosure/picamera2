import errno
from logging import getLogger
from typing import Any, Dict

import libcamera

_log = getLogger(__name__)


def errno_handle(code: int, callname: str) -> None:
    """Convert an errno to a string.

    If code is >= 0, it will log a debug message and otherwise noop
    If code is < 0, it will log an error message and raise a ``RuntimeError``
    """
    if code >= 0:
        str_rep = "Success"
    else:
        str_rep = errno.errorcode.get(-code, "Unknown error")
    formatted = f"{callname} - {str_rep} ({code})"

    if code >= 0:
        _log.debug(formatted)
    else:
        _log.error(formatted)
        raise RuntimeError(formatted)


def _convert_from_libcamera_type(value):
    if isinstance(value, libcamera.Rectangle):
        value = (value.x, value.y, value.width, value.height)
    elif isinstance(value, libcamera.Size):
        value = (value.width, value.height)
    elif isinstance(value, (tuple, list)):
        value = [_convert_from_libcamera_type(v) for v in value]
    return value


def lc_unpack(lc_dict) -> Dict[str, Any]:
    unpacked = {}
    for k, v in lc_dict.items():
        unpacked[k.name] = _convert_from_libcamera_type(v)
    return unpacked


def lc_unpack_controls(lc_dict) -> Dict[str, Any]:
    unpacked = {}
    for k, v in lc_dict.items():
        unpacked[k.name] = (k, v)
    return unpacked


LCTransform = libcamera._libcamera.Transform


def libcamera_transforms_eq(t1: LCTransform, t2: LCTransform) -> bool:
    """Return ``True`` if the two transforms are equivalent."""
    return (
        t1.hflip == t2.hflip and t1.vflip == t2.vflip and t1.transpose == t2.transpose
    )


def libcamera_color_spaces_eq(c1, c2) -> bool:
    """Return ``True`` if the two color spaces are equivalent."""
    return (
        c1.primaries == c2.primaries
        and c1.transferFunction == c2.transferFunction
        and c1.ycbcrEncoding == c2.ycbcrEncoding
        and c1.range == c2.range
    )


def lc_return_code_helper(return_code: int, method: str) -> None:
    """Decode and process a libcamera return code.

    These are generally encoded as negative numbers which map to
    errno values. This function raises a RuntimeError if the return
    code is negative, and tries to make the result more ledgible.
    """
    if return_code < 0:
        error_name = errno.errorcode.get(-return_code, "No Errno")
        raise RuntimeError(f"Error calling {method}: {return_code} ({error_name})")
