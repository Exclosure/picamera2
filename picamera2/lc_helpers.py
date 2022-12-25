from typing import Dict, Any

import libcamera


def _convert_from_libcamera_type(value):
    if isinstance(value, libcamera.Rectangle):
        value = (value.x, value.y, value.width, value.height)
    elif isinstance(value, libcamera.Size):
        value = (value.width, value.height)
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