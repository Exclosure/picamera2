from __future__ import annotations

import io
import mmap
import threading
from abc import ABC, abstractmethod
from concurrent.futures import Future
from dataclasses import dataclass, field
from functools import partial
from logging import getLogger
from typing import Any, Callable, Dict

import numpy as np
from PIL import Image

import picamera2.formats as formats
from picamera2 import formats
from picamera2.lc_helpers import lc_unpack

_log = getLogger(__name__)


class MappedBuffer:
    def __init__(self, request, stream):
        stream = request.camera.stream_map[stream]
        self.__fb = request.request.buffers[stream]

    def __enter__(self):
        # Check if the buffer is contiguous and find the total length.
        fd = self.__fb.planes[0].fd
        planes_metadata = self.__fb.metadata.planes
        buflen = 0
        for p, p_metadata in zip(self.__fb.planes, planes_metadata):
            # bytes_used is the same as p.length for regular frames, but correctly reflects
            # the compressed image size for MJPEG cameras.
            buflen = buflen + p_metadata.bytes_used
            if fd != p.fd:
                raise RuntimeError("_MappedBuffer: Cannot map non-contiguous buffer!")

        self.__mm = mmap.mmap(
            fd, buflen, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE
        )
        return self.__mm

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if self.__mm is not None:
            self.__mm.close()


# TODO (meawoppl) - Flatten into the above class using an np array view.
# or at the very least actully use the context manager protocol it reps.
class MappedArray:
    def __init__(self, request, stream, reshape=True):
        self.__request = request
        self.__stream = stream
        self.__buffer = MappedBuffer(request, stream)
        self.__array = None
        self.__reshape = reshape

    def __enter__(self):
        b = self.__buffer.__enter__()
        array = np.array(b, copy=False, dtype=np.uint8)

        if self.__reshape:
            config = self.__request.camera.camera_config[self.__stream]
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
                    array = array[:, : w * 3]
                array = array.reshape((h, w, 3))
            elif fmt in ("XBGR8888", "XRGB8888"):
                if stride != w * 4:
                    array = array.reshape((h, stride))
                    array = array[:, : w * 4]
                array = array.reshape((h, w, 4))
            elif fmt in ("YUV420", "YVU420"):
                # Returning YUV420 as an image of 50% greater height (the extra bit continaing
                # the U/V data) is useful because OpenCV can convert it to RGB for us quite
                # efficiently. We leave any packing in there, however, as it would be easier
                # to remove that after conversion to RGB (if that's what the caller does).
                array = array.reshape((h * 3 // 2, stride))
            elif formats.is_raw(fmt):
                array = array.reshape((h, stride))
            else:
                raise RuntimeError("Format " + fmt + " not supported")

        self.__array = array
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if self.__array is not None:
            del self.__array
        self.__buffer.__exit__(exc_type, exc_value, exc_traceback)

    @property
    def array(self):
        return self.__array


class AbstractCompletedRequest(ABC):
    @abstractmethod
    def get_config(self, name: str) -> Dict[str, Any]:
        raise NotImplementedError()

    @abstractmethod
    def make_buffer(self, name: str) -> np.ndarray:
        raise NotImplementedError()

    @abstractmethod
    def make_metadata(self) -> Dict[str, Any]:
        raise NotImplementedError()

    def make_array(self, name: str) -> np.ndarray:
        """Make a 2d numpy array from the named stream's buffer."""
        config = self.get_config()
        array = self.make_buffer(name)
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

    def make_image(self, name: str) -> Image.Image:
        """Make a PIL image from the named stream's buffer."""
        config = self.get_config()
        fmt = config["format"]
        if fmt == "MJPEG":
            buffer = self.make_buffer(name)
            return Image.open(io.BytesIO(buffer))
        else:
            rgb = self.make_array(name)
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


# TODO(meawoppl) - Make Completed Requests only exist inside of a context manager
# This remove all the bizzare locking and reference counting we are doing here manually
class CompletedRequest(AbstractCompletedRequest):
    def __init__(self, lc_request, config: dict, cleanup: Callable[[], None]):
        self.request = lc_request
        self.ref_count = 1
        self.lock = threading.Lock()
        self.config = config
        self.cleanup = cleanup

    def acquire(self):
        """Acquire a reference to this completed request, which stops it being recycled back to
        the camera system.
        """
        with self.lock:
            if self.ref_count == 0:
                raise RuntimeError("CompletedRequest: acquiring lock with ref_count 0")
            self.ref_count += 1

    def release(self):
        """Release this completed frame back to the camera system (once its reference count
        reaches zero).
        """
        with self.lock:
            self.ref_count -= 1
            if self.ref_count < 0:
                raise RuntimeError("CompletedRequest: lock now has negative ref_count")

            if self.ref_count > 0:
                return

            self.cleanup()
            self.request = None

    def get_config(self, name: str) -> Dict[str, Any]:
        """Fetch the configuration for the named stream."""
        return self.config[name]

    def make_buffer(self, name: str) -> np.ndarray:
        """Make a 1d numpy array from the named stream's buffer."""
        with MappedBuffer(self, name) as b:
            return np.array(b, dtype=np.uint8)

    def get_metadata(self) -> Dict[str, Any]:
        """Fetch the metadata corresponding to this completed request."""
        return lc_unpack(self.request.metadata)


@dataclass
class LoopTask:
    call: Callable[[CompletedRequest], Any] | callable[[], Any]

    needs_request: bool = True

    future: Future = field(init=False, default_factory=Future)

    @classmethod
    def with_request(cls, call, *args):
        return cls(call=partial(call, *args), needs_request=True)

    @classmethod
    def without_request(cls, call, *args):
        return cls(call=partial(call, *args), needs_request=False)

    def __post_init__(self):
        self.future.set_running_or_notify_cancel()
