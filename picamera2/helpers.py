import io
from logging import getLogger

import numpy as np
from PIL import Image

from picamera2 import formats


class Helpers:
    """This class implements functionality required by the CompletedRequest methods, but
    in such a way that it can be usefully accessed even without a CompletedRequest object."""

    @staticmethod
    def make_array(buffer: np.ndarray, config: dict):
        """Make a 2d numpy array from the named stream's buffer."""
        array = buffer
        fmt = config["format"]
        w, h = config["size"]
        stride = config["stride"]

        # Turning the 1d array into a 2d image-like array only works if the
        # image stride (which is in bytes) is a whole number of pixels. Even
        # then, if they don't match exactly you will get "padding" down the RHS.
        # Working around this requires another expensive copy of all the data.
        if fmt in ("BGR888", "RGB888"):
            if stride != w * 3:
                array = array.reshape((h, stride))
                array = np.asarray(array[:, : w * 3], order="C")
            image = array.reshape((h, w, 3))
        elif fmt in ("XBGR8888", "XRGB8888"):
            if stride != w * 4:
                array = array.reshape((h, stride))
                array = np.asarray(array[:, : w * 4], order="C")
            image = array.reshape((h, w, 4))
        elif fmt in ("YUV420", "YVU420"):
            # Returning YUV420 as an image of 50% greater height (the extra bit continaing
            # the U/V data) is useful because OpenCV can convert it to RGB for us quite
            # efficiently. We leave any packing in there, however, as it would be easier
            # to remove that after conversion to RGB (if that's what the caller does).
            image = array.reshape((h * 3 // 2, stride))
        elif fmt in ("YUYV", "YVYU", "UYVY", "VYUY"):
            # These dimensions seem a bit strange, but mean that
            # cv2.cvtColor(image, cv2.COLOR_YUV2BGR_YUYV) will convert directly to RGB.
            image = array.reshape(h, stride // 2, 2)
        elif fmt == "MJPEG":
            image = np.array(Image.open(io.BytesIO(array)))
        elif formats.is_raw(fmt):
            image = array.reshape((h, stride))
        else:
            raise RuntimeError("Format " + fmt + " not supported")
        return image

    @staticmethod
    def make_image(buffer: np.ndarray, config: dict, width=None, height=None):
        """Make a PIL image from the named stream's buffer."""
        fmt = config["format"]
        if fmt == "MJPEG":
            return Image.open(io.BytesIO(buffer))
        else:
            rgb = Helpers.make_array(buffer, config)
        mode_lookup = {
            "RGB888": "BGR",
            "BGR888": "RGB",
            "XBGR8888": "RGBA",
            "XRGB8888": "BGRX",
        }
        if fmt not in mode_lookup:
            raise RuntimeError(f"Stream format {fmt} not supported for PIL images")
        mode = mode_lookup[fmt]
        pil_img = Image.frombuffer(
            "RGB", (rgb.shape[1], rgb.shape[0]), rgb, "raw", mode, 0, 1
        )
        if width is None:
            width = rgb.shape[1]
        if height is None:
            height = rgb.shape[0]
        if width != rgb.shape[1] or height != rgb.shape[0]:
            # This will be slow. Consider requesting camera images of this size in the first place!
            pil_img = pil_img.resize((width, height))
        return pil_img
