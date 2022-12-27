#!/usr/bin/python3
"""picamera2 main class"""
from __future__ import annotations

import json
import logging
import os
import selectors
import tempfile
import threading
from collections import deque
from concurrent.futures import Future
from dataclasses import dataclass
from typing import Any, Callable, Deque, Dict, List, Tuple

import libcamera
import numpy as np
from PIL import Image

import picamera2.formats as formats
from picamera2.configuration import CameraConfiguration
from picamera2.controls import Controls
from picamera2.lc_helpers import lc_unpack, lc_unpack_controls
from picamera2.previews import NullPreview
from picamera2.request import CompletedRequest, LoopTask
from picamera2.sensor_format import SensorFormat
from picamera2.stream_config import (
    align_stream,
    check_stream_config,
    make_initial_stream_config,
)

STILL = libcamera.StreamRole.StillCapture
RAW = libcamera.StreamRole.Raw
VIDEO = libcamera.StreamRole.VideoRecording
VIEWFINDER = libcamera.StreamRole.Viewfinder

_log = logging.getLogger(__name__)


# TODO(meawoppl) doc these arrtibutes
@dataclass
class CameraInfo:
    id: str

    model: str

    location: str

    rotation: int

    @staticmethod
    def global_camera_info() -> List[CameraInfo]:
        """
        Return Id string and Model name for all attached cameras, one dict per camera,
        and ordered correctly by camera number. Also return the location and rotation
        of the camera when known, as these may help distinguish which is which.
        """
        infos = []
        for cam in libcamera.CameraManager.singleton().cameras:
            name_to_val = {
                k.name.lower(): v
                for k, v in cam.properties.items()
                if k.name in ("Model", "Location", "Rotation")
            }
            name_to_val["id"] = cam.id
            infos.append(CameraInfo(**name_to_val))
        return infos

    @staticmethod
    def n_cameras() -> int:
        """Return the number of attached cameras."""
        return len(libcamera.CameraManager.singleton().cameras)

    def requires_camera(n: int = 1):
        if CameraInfo.n_cameras() < n:
            _log.error(
                "Camera(s) not found (Do not forget to disable legacy camera with raspi-config)."
            )
            raise RuntimeError(
                "Camera(s) not found (Do not forget to disable legacy camera with raspi-config)."
            )


class CameraManager:
    cameras: Dict[int, Picamera2]

    def __init__(self):
        self.running = False
        self.cameras = {}
        self._lock = threading.Lock()

    def setup(self):
        self.cms = libcamera.CameraManager.singleton()
        self.thread = threading.Thread(target=self.listen, daemon=True)
        self.running = True
        self.thread.start()

    def add(self, index: int, camera: Picamera2):
        with self._lock:
            self.cameras[index] = camera
            if not self.running:
                self.setup()

    def cleanup(self, index: int):
        flag = False
        with self._lock:
            del self.cameras[index]
            if self.cameras == {}:
                self.running = False
                flag = True
        if flag:
            self.thread.join()
            self.cms = None

    def listen(self):
        sel = selectors.DefaultSelector()
        sel.register(self.cms.event_fd, selectors.EVENT_READ, self.handle_request)

        while self.running:
            events = sel.select(0.2)
            for key, _ in events:
                callback = key.data
                callback()

        sel.unregister(self.cms.event_fd)
        self.cms = None

    def handle_request(self, flushid=None):
        """Handle requests"""
        with self._lock:
            cams = set()
            for req in self.cms.get_ready_requests():
                if (
                    req.status == libcamera.Request.Status.Complete
                    and req.cookie != flushid
                ):
                    cams.add(req.cookie)

                    self.cameras[req.cookie].add_completed_request(
                        CompletedRequest(req, self.cameras[req.cookie])
                    )
            # OS based file pipes seem really overkill for this.
            # TODO(meawoppl) - Convert to queue primitive
            for c in cams:
                os.write(self.cameras[c].notifyme_w, b"\x00")


class Picamera2:
    """Welcome to the PiCamera2 class."""

    _cm = CameraManager()

    @staticmethod
    def load_tuning_file(tuning_file, dir=None):
        """Load the named tuning file.

        If dir is given, then only that directory is checked,
        otherwise a list of likely installation directories is searched

        :param tuning_file: Tuning file
        :type tuning_file: str
        :param dir: Directory of tuning file, defaults to None
        :type dir: str, optional
        :raises RuntimeError: Produced if tuning file not found
        :return: Dictionary of tuning file
        :rtype: dict
        """
        if dir is not None:
            dirs = [dir]
        else:
            dirs = [
                "/home/pi/libcamera/src/ipa/raspberrypi/data",
                "/usr/local/share/libcamera/ipa/raspberrypi",
                "/usr/share/libcamera/ipa/raspberrypi",
            ]
        for dir in dirs:
            file = os.path.join(dir, tuning_file)
            if os.path.isfile(file):
                with open(file, "r") as fp:
                    return json.load(fp)
        raise RuntimeError("Tuning file not found")

    @staticmethod
    def find_tuning_algo(tuning: dict, name: str) -> dict:
        """
        Return the parameters for the named algorithm in the given camera tuning.

        :param tuning: The camera tuning object
        :type tuning: dict
        :param name: The name of the algorithm
        :type name: str
        :rtype: dict
        """
        version = tuning.get("version", 1)
        if version == 1:
            return tuning[name]
        return next(algo for algo in tuning["algorithms"] if name in algo)[name]

    def __init__(self, camera_num=0, tuning=None):
        """Initialise camera system and open the camera for use.

        :param camera_num: Camera index, defaults to 0
        :type camera_num: int, optional
        :param tuning: Tuning filename, defaults to None
        :type tuning: str, optional
        :raises RuntimeError: Init didn't complete
        """
        tuning_file = None
        if tuning is not None:
            if isinstance(tuning, str):
                os.environ["LIBCAMERA_RPI_TUNING_FILE"] = tuning
            else:
                tuning_file = tempfile.NamedTemporaryFile("w")
                json.dump(tuning, tuning_file)
                tuning_file.flush()  # but leave it open as closing it will delete it
                os.environ["LIBCAMERA_RPI_TUNING_FILE"] = tuning_file.name
        else:
            os.environ.pop("LIBCAMERA_RPI_TUNING_FILE", None)  # Use default tuning
        self.notifyme_r, self.notifyme_w = os.pipe2(os.O_NONBLOCK)
        self.notifymeread = os.fdopen(self.notifyme_r, "rb")
        self._cm.add(camera_num, self)
        self.camera_idx = camera_num
        self._requests = deque()
        self._request_callbacks = []
        self._reset_flags()
        try:
            self._open_camera()
            _log.debug(f"{self.camera_manager}")
            self.preview_configuration = self.create_preview_configuration()
            self.still_configuration = self.create_still_configuration()
            self.video_configuration = self.create_video_configuration()
        except Exception as e:
            _log.error("Camera __init__ sequence did not complete.", exc_info=e)
            raise RuntimeError("Camera __init__ sequence did not complete.") from e
        finally:
            if tuning_file is not None:
                tuning_file.close()  # delete the temporary file

    @property
    def camera_manager(self):
        return Picamera2._cm.cms

    def add_request_callback(self, callback: Callable[[CompletedRequest], None]):
        """Add a callback to be called when every request completes.

        Note that the request is only valid within the callback, and will be
        deallocated after the callback returns.

        :param callback: The callback to be called
        :type callback: Callable[[CompletedRequest], None]
        """
        self._request_callbacks.append(callback)

    def _reset_flags(self) -> None:
        self.camera = None
        self.is_open = False
        self.camera_ctrl_info = {}
        self._preview = None
        self.camera_config = None
        self.libcamera_config = None
        self.streams = None
        self.stream_map = None
        self.started = False
        self.stop_count = 0
        self.configure_count = 0
        self.frames = 0
        self._task_deque: Deque[LoopTask] = deque()
        self.options = {}
        self.post_callback = None
        self.camera_properties_ = {}
        self.controls = Controls(self)
        self.sensor_modes_ = None

    @property
    def preview_configuration(self) -> CameraConfiguration:
        return self.preview_configuration_

    @preview_configuration.setter
    def preview_configuration(self, value):
        self.preview_configuration_ = CameraConfiguration(value, self)

    @property
    def still_configuration(self) -> CameraConfiguration:
        return self.still_configuration_

    @still_configuration.setter
    def still_configuration(self, value):
        self.still_configuration_ = CameraConfiguration(value, self)

    @property
    def video_configuration(self) -> CameraConfiguration:
        return self.video_configuration_

    @video_configuration.setter
    def video_configuration(self, value):
        self.video_configuration_ = CameraConfiguration(value, self)

    @property
    def asynchronous(self) -> bool:
        """True if there is threaded operation

        :return: Thread operation state
        :rtype: bool
        """
        return (
            self._preview is not None
            and getattr(self._preview, "thread", None) is not None
            and self._preview.thread.is_alive()
        )

    @property
    def camera_properties(self) -> dict:
        """Camera properties

        :return: Camera properties
        :rtype: dict
        """
        return {} if self.camera is None else self.camera_properties_

    @property
    def camera_controls(self) -> dict:
        return {
            k: (v[1].min, v[1].max, v[1].default)
            for k, v in self.camera_ctrl_info.items()
        }

    def __enter__(self):
        """Used for allowing use with context manager

        :return: self
        :rtype: Picamera2
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_traceback):
        """Used for allowing use with context manager

        :param exc_type: Exception type
        :type exc_type: Type[BaseException]
        :param exc_val: Exception
        :type exc_val: BaseException
        :param exc_traceback: Traceback
        :type exc_traceback: TracebackType
        """
        self.close()

    def __del__(self):
        """Without this libcamera will complain if we shut down without closing the camera."""
        _log.warning(f"__del__ call responsible for cleanup of {self}")
        self.close()

    def _grab_camera(self, idx: str | int):
        if isinstance(idx, str):
            try:
                return self.camera_manager.get(idx)
            except Exception:
                return self.camera_manager.find(idx)
        elif isinstance(idx, int):
            return self.camera_manager.cameras[idx]

    def requires_camera(self):
        if self.camera is None:
            message = "Initialization failed."
            _log.error(message)
            raise RuntimeError(message)

    def _initialize_camera(self) -> None:
        """Initialize camera

        :raises RuntimeError: Failure to initialise camera
        """
        CameraInfo.requires_camera(1)
        self.camera = self._grab_camera(self.camera_idx)
        self.requires_camera()

        self.__identify_camera()
        self.camera_ctrl_info = lc_unpack_controls(self.camera.controls)
        self.camera_properties_ = lc_unpack(self.camera.properties)

        # The next two lines could be placed elsewhere?
        self.sensor_resolution = self.camera_properties_["PixelArraySize"]
        self.sensor_format = str(
            self.camera.generate_configuration([RAW]).at(0).pixel_format
        )

        _log.info("Initialization successful.")

    def __identify_camera(self):
        # TODO(meawoppl) make this a helper on the camera_manager
        for idx, address in enumerate(self.camera_manager.cameras):
            if address == self.camera:
                self.camera_idx = idx
                break

    def _open_camera(self) -> None:
        """Tries to open camera

        :raises RuntimeError: Failed to setup camera
        """
        self._initialize_camera()

        acq_code = self.camera.acquire()
        if acq_code != 0:
            raise RuntimeError(f"camera.acquire() returned unexpected code: {acq_code}")

        self.is_open = True
        _log.info("Camera now open.")

    @property
    def sensor_modes(self) -> list:
        """The available sensor modes

        When called for the first time this will reconfigure the camera
        in order to read the modes.
        """
        if self.sensor_modes_ is not None:
            return self.sensor_modes_

        raw_config = self.camera.generate_configuration([libcamera.StreamRole.Raw])
        raw_formats = raw_config.at(0).formats
        self.sensor_modes_ = []

        for pix in raw_formats.pixel_formats:
            name = str(pix)
            if not formats.is_raw(name):
                # Not a raw sensor so we can't deduce much about it. Quote the name and carry on.
                self.sensor_modes_.append({"format": name})
                continue
            fmt = SensorFormat(name)
            all_format = {}
            all_format["format"] = fmt
            all_format["unpacked"] = fmt.unpacked
            all_format["bit_depth"] = fmt.bit_depth
            for size in raw_formats.sizes(pix):
                cam_mode = all_format.copy()
                cam_mode["size"] = (size.width, size.height)
                temp_config = self.create_preview_configuration(
                    raw={"format": str(pix), "size": cam_mode["size"]}
                )
                self.configure(temp_config)
                frameDurationMin = self.camera_controls["FrameDurationLimits"][0]
                cam_mode["fps"] = round(1e6 / frameDurationMin, 2)
                cam_mode["crop_limits"] = self.camera_properties["ScalerCropMaximum"]
                cam_mode["exposure_limits"] = tuple(
                    [i for i in self.camera_controls["ExposureTime"] if i != 0]
                )
                self.sensor_modes_.append(cam_mode)
        return self.sensor_modes_

    # TODO(meawoppl) we don't really support previews, so change the language here
    def start_preview(self) -> None:
        """
        Start the preview loop.
        """
        if self._preview:
            raise RuntimeError("An event loop is already running")

        preview = NullPreview()
        preview.start(self)
        self._preview = preview

    def stop_preview(self) -> None:
        """Stop preview

        :raises RuntimeError: Unable to stop preview
        """
        if not self._preview:
            raise RuntimeError("No preview specified.")

        try:
            self._preview.stop()
            self._preview = None
        except Exception:
            raise RuntimeError("Unable to stop preview.")

    def close(self) -> None:
        """Close camera

        :raises RuntimeError: Closing failed
        """
        if self._preview:
            self.stop_preview()
        if not self.is_open:
            return

        self.stop()
        release_code = self.camera.release()
        if release_code < 0:
            raise RuntimeError(f"Failed to release camera ({release_code})")
        self._cm.cleanup(self.camera_idx)
        self.is_open = False
        self.streams = None
        self.stream_map = None
        self.camera = None
        self.camera_ctrl_info = None
        self.camera_config = None
        self.libcamera_config = None
        self.preview_configuration_ = None
        self.still_configuration_ = None
        self.video_configuration_ = None
        self.allocator = None
        self.notifymeread.close()
        os.close(self.notifyme_w)
        _log.info("Camera closed successfully.")

    # TODO(meawoppl) - What is this doing here?
    _raw_stream_ignore_list = [
        "bit_depth",
        "crop_limits",
        "exposure_limits",
        "fps",
        "unpacked",
    ]

    # TODO(meawoppl) - These can likely be made static/hoisted
    def create_preview_configuration(
        self,
        main={},
        lores=None,
        raw=None,
        transform=libcamera.Transform(),
        colour_space=libcamera.ColorSpace.Sycc(),
        buffer_count=4,
        controls={},
    ) -> dict:
        """Make a configuration suitable for camera preview."""
        self.requires_camera()
        main = make_initial_stream_config(
            {"format": "XBGR8888", "size": (640, 480)}, main
        )
        align_stream(main, optimal=False)
        lores = make_initial_stream_config(
            {"format": "YUV420", "size": main["size"]}, lores
        )
        if lores is not None:
            align_stream(lores, optimal=False)
        raw = make_initial_stream_config(
            {"format": self.sensor_format, "size": main["size"]},
            raw,
            self._raw_stream_ignore_list,
        )
        # Let the framerate vary from 12fps to as fast as possible.
        if (
            "NoiseReductionMode" in self.camera_controls
            and "FrameDurationLimits" in self.camera_controls
        ):
            controls = {
                "NoiseReductionMode": libcamera.controls.draft.NoiseReductionModeEnum.Minimal,
                "FrameDurationLimits": (100, 83333),
            } | controls
        config = {
            "use_case": "preview",
            "transform": transform,
            "colour_space": colour_space,
            "buffer_count": buffer_count,
            "main": main,
            "lores": lores,
            "raw": raw,
            "controls": controls,
        }
        return config

    # TODO(meawoppl) - These can likely be made static/hoisted
    def create_still_configuration(
        self,
        main={},
        lores=None,
        raw=None,
        transform=libcamera.Transform(),
        colour_space=libcamera.ColorSpace.Sycc(),
        buffer_count=1,
        controls={},
    ) -> dict:
        """Make a configuration suitable for still image capture. Default to 2 buffers, as the Gl preview would need them."""
        self.requires_camera()
        main = make_initial_stream_config(
            {"format": "BGR888", "size": self.sensor_resolution}, main
        )
        align_stream(main, optimal=False)
        lores = make_initial_stream_config(
            {"format": "YUV420", "size": main["size"]}, lores
        )
        if lores is not None:
            align_stream(lores, optimal=False)
        raw = make_initial_stream_config(
            {"format": self.sensor_format, "size": main["size"]}, raw
        )
        # Let the framerate span the entire possible range of the sensor.
        if (
            "NoiseReductionMode" in self.camera_controls
            and "FrameDurationLimits" in self.camera_controls
        ):
            controls = {
                "NoiseReductionMode": libcamera.controls.draft.NoiseReductionModeEnum.HighQuality,
                "FrameDurationLimits": (100, 1000000 * 1000),
            } | controls
        config = {
            "use_case": "still",
            "transform": transform,
            "colour_space": colour_space,
            "buffer_count": buffer_count,
            "main": main,
            "lores": lores,
            "raw": raw,
            "controls": controls,
        }
        return config

    # TODO(meawoppl) - These can likely be made static/hoisted
    def create_video_configuration(
        self,
        main={},
        lores=None,
        raw=None,
        transform=libcamera.Transform(),
        colour_space=None,
        buffer_count=6,
        controls={},
    ) -> dict:
        """Make a configuration suitable for video recording."""
        self.requires_camera()
        main = make_initial_stream_config(
            {"format": "XBGR8888", "size": (1280, 720)}, main
        )
        align_stream(main, optimal=False)
        lores = make_initial_stream_config(
            {"format": "YUV420", "size": main["size"]}, lores
        )
        if lores is not None:
            align_stream(lores, optimal=False)
        raw = make_initial_stream_config(
            {"format": self.sensor_format, "size": main["size"]}, raw
        )
        if colour_space is None:
            # Choose default colour space according to the video resolution.
            if formats.is_RGB(main["format"]):
                # There's a bug down in some driver where it won't accept anything other than
                # sRGB or JPEG as the colour space for an RGB stream. So until that is fixed:
                colour_space = libcamera.ColorSpace.Sycc()
            elif main["size"][0] < 1280 or main["size"][1] < 720:
                colour_space = libcamera.ColorSpace.Smpte170m()
            else:
                colour_space = libcamera.ColorSpace.Rec709()
        if (
            "NoiseReductionMode" in self.camera_controls
            and "FrameDurationLimits" in self.camera_controls
        ):
            controls = {
                "NoiseReductionMode": libcamera.controls.draft.NoiseReductionModeEnum.Fast,
                "FrameDurationLimits": (33333, 33333),
            } | controls
        config = {
            "use_case": "video",
            "transform": transform,
            "colour_space": colour_space,
            "buffer_count": buffer_count,
            "main": main,
            "lores": lores,
            "raw": raw,
            "controls": controls,
        }
        return config

    # TODO(meawoppl) - dataclass __post_init__ materials
    def check_camera_config(self, camera_config: dict) -> None:
        required_keys = ["colour_space", "transform", "main", "lores", "raw"]
        for name in required_keys:
            if name not in camera_config:
                raise RuntimeError(f"'{name}' key expected in camera configuration")

        # Check the entire camera configuration for errors.
        if not isinstance(
            camera_config["colour_space"], libcamera._libcamera.ColorSpace
        ):
            raise RuntimeError("Colour space has incorrect type")
        if not isinstance(camera_config["transform"], libcamera._libcamera.Transform):
            raise RuntimeError("Transform has incorrect type")

        check_stream_config(camera_config["main"], "main")
        if camera_config["lores"] is not None:
            check_stream_config(camera_config["lores"], "lores")
            main_w, main_h = camera_config["main"]["size"]
            lores_w, lores_h = camera_config["lores"]["size"]
            if lores_w > main_w or lores_h > main_h:
                raise RuntimeError("lores stream dimensions may not exceed main stream")
            if not formats.is_YUV(camera_config["lores"]["format"]):
                raise RuntimeError("lores stream must be YUV")
        if camera_config["raw"] is not None:
            check_stream_config(camera_config["raw"], "raw")

    # TODO(meawoppl) - Obviated by dataclasses
    @staticmethod
    def _update_libcamera_stream_config(
        libcamera_stream_config, stream_config, buffer_count
    ) -> None:
        # Update the libcamera stream config with ours.
        libcamera_stream_config.size = libcamera.Size(
            stream_config["size"][0], stream_config["size"][1]
        )
        libcamera_stream_config.pixel_format = libcamera.PixelFormat(
            stream_config["format"]
        )
        libcamera_stream_config.buffer_count = buffer_count

    # TODO(meawoppl) - Obviated by dataclasses
    def _make_libcamera_config(self, camera_config):
        # Make a libcamera configuration object from our Python configuration.

        # We will create each stream with the "viewfinder" role just to get the stream
        # configuration objects, and note the positions our named streams will have in
        # libcamera's stream list.
        roles = [VIEWFINDER]
        index = 1
        self.main_index = 0
        self.lores_index = -1
        self.raw_index = -1
        if camera_config["lores"] is not None:
            self.lores_index = index
            index += 1
            roles += [VIEWFINDER]
        if camera_config["raw"] is not None:
            self.raw_index = index
            roles += [RAW]

        # Make the libcamera configuration, and then we'll write all our parameters over
        # the ones it gave us.
        libcamera_config = self.camera.generate_configuration(roles)
        libcamera_config.transform = camera_config["transform"]
        buffer_count = camera_config["buffer_count"]
        self._update_libcamera_stream_config(
            libcamera_config.at(self.main_index), camera_config["main"], buffer_count
        )
        libcamera_config.at(self.main_index).color_space = camera_config["colour_space"]
        if self.lores_index >= 0:
            self._update_libcamera_stream_config(
                libcamera_config.at(self.lores_index),
                camera_config["lores"],
                buffer_count,
            )
            libcamera_config.at(self.lores_index).color_space = camera_config[
                "colour_space"
            ]
        if self.raw_index >= 0:
            self._update_libcamera_stream_config(
                libcamera_config.at(self.raw_index), camera_config["raw"], buffer_count
            )
            libcamera_config.at(self.raw_index).color_space = libcamera.ColorSpace.Raw()

        return libcamera_config

    def _make_requests(self) -> List[libcamera.Request]:
        """Make libcamera request objects.

        Makes as many as the number of buffers in the stream with the smallest number of buffers.

        :raises RuntimeError: Failure
        :return: requests
        :rtype: List[libcamera.Request]
        """
        num_requests = min(
            [len(self.allocator.buffers(stream)) for stream in self.streams]
        )
        requests = []
        for i in range(num_requests):
            request = self.camera.create_request(self.camera_idx)
            if request is None:
                raise RuntimeError("Could not create request")

            for stream in self.streams:
                if request.add_buffer(stream, self.allocator.buffers(stream)[i]) < 0:
                    raise RuntimeError("Failed to set request buffer")
            requests.append(request)
        return requests

    def _update_stream_config(self, stream_config, libcamera_stream_config) -> None:
        # Update our stream config from libcamera's.
        stream_config["format"] = str(libcamera_stream_config.pixel_format)
        stream_config["size"] = (
            libcamera_stream_config.size.width,
            libcamera_stream_config.size.height,
        )
        stream_config["stride"] = libcamera_stream_config.stride
        stream_config["framesize"] = libcamera_stream_config.frame_size

    def _update_camera_config(self, camera_config, libcamera_config) -> None:
        """Update our camera config from libcamera's.

        :param camera_config: Camera configuration
        :type camera_config: dict
        :param libcamera_config: libcamera configuration
        :type libcamera_config: dict
        """
        camera_config["transform"] = libcamera_config.transform
        camera_config["colour_space"] = libcamera_config.at(0).color_space
        self._update_stream_config(camera_config["main"], libcamera_config.at(0))
        if self.lores_index >= 0:
            self._update_stream_config(
                camera_config["lores"], libcamera_config.at(self.lores_index)
            )
        if self.raw_index >= 0:
            self._update_stream_config(
                camera_config["raw"], libcamera_config.at(self.raw_index)
            )

    def _configure(self, camera_config="preview") -> None:
        """Configure the camera system with the given configuration.

        :param camera_config: Configuration, defaults to the 'preview' configuration
        :type camera_config: dict, string or CameraConfiguration, optional
        :raises RuntimeError: Failed to configure
        """
        if self.started:
            raise RuntimeError("Camera must be stopped before configuring")
        initial_config = camera_config
        if isinstance(initial_config, str):
            if initial_config == "preview":
                camera_config = self.preview_configuration
            elif initial_config == "still":
                camera_config = self.still_configuration
            else:
                camera_config = self.video_configuration
        elif isinstance(initial_config, dict):
            camera_config = camera_config.copy()
        if isinstance(camera_config, CameraConfiguration):
            if camera_config.raw is not None and camera_config.raw.format is None:
                camera_config.raw.format = self.sensor_format
            # We expect values to have been set for any lores/raw streams.
            camera_config = camera_config.make_dict()
        if camera_config is None:
            camera_config = self.create_preview_configuration()

        # Mark ourselves as unconfigured.
        self.libcamera_config = None
        self.camera_config = None

        # Check the config and turn it into a libcamera config.
        self.check_camera_config(camera_config)
        libcamera_config = self._make_libcamera_config(camera_config)

        # Check that libcamera is happy with it.
        status = libcamera_config.validate()
        self._update_camera_config(camera_config, libcamera_config)
        _log.debug(f"Requesting configuration: {camera_config}")
        if status == libcamera.CameraConfiguration.Status.Invalid:
            raise RuntimeError("Invalid camera configuration: {}".format(camera_config))
        elif status == libcamera.CameraConfiguration.Status.Adjusted:
            _log.info("Camera configuration has been adjusted!")

        # Configure libcamera.
        if self.camera.configure(libcamera_config):
            raise RuntimeError("Configuration failed: {}".format(camera_config))
        _log.info("Configuration successful!")
        _log.debug(f"Final configuration: {camera_config}")

        # Update the controls and properties list as some of the values may have changed.
        self.camera_ctrl_info = lc_unpack_controls(self.camera.controls)
        self.camera_properties_ = lc_unpack(self.camera.properties)

        # Record which libcamera stream goes with which of our names.
        self.stream_map = {"main": libcamera_config.at(0).stream}
        self.stream_map["lores"] = (
            libcamera_config.at(self.lores_index).stream
            if self.lores_index >= 0
            else None
        )
        self.stream_map["raw"] = (
            libcamera_config.at(self.raw_index).stream if self.raw_index >= 0 else None
        )
        _log.debug(f"Streams: {self.stream_map}")

        # Allocate all the frame buffers.
        self.streams = [stream_config.stream for stream_config in libcamera_config]

        # TODO(meawoppl) - can be taken off public and used in the 1 function
        # that calls it.
        self.allocator = libcamera.FrameBufferAllocator(self.camera)
        for i, stream in enumerate(self.streams):
            if self.allocator.allocate(stream) < 0:
                _log.critical("Failed to allocate buffers.")
                raise RuntimeError("Failed to allocate buffers.")
            msg = f"Allocated {len(self.allocator.buffers(stream))} buffers for stream {i}."
            _log.debug(msg)
        # Mark ourselves as configured.
        self.libcamera_config = libcamera_config
        self.camera_config = camera_config
        # Fill in the embedded configuration structures if those were used.
        if initial_config == "preview":
            self.preview_configuration.update(camera_config)
        elif initial_config == "still":
            self.still_configuration.update(camera_config)
        else:
            self.video_configuration.update(camera_config)
        # Set the controls directly so as to overwrite whatever is there.
        self.controls.set_controls(self.camera_config["controls"])
        self.configure_count += 1

    def configure(self, camera_config="preview") -> None:
        """Configure the camera system with the given configuration."""
        self._configure(camera_config)

    def camera_configuration(self) -> dict:
        """Return the camera configuration."""
        return self.camera_config

    def stream_configuration(self, name="main") -> dict:
        """Return the stream configuration for the named stream."""
        return self.camera_config[name]

    def _start(self) -> None:
        """Start the camera system running."""
        if self.camera_config is None:
            raise RuntimeError("Camera has not been configured")
        if self.started:
            raise RuntimeError("Camera already started")
        controls = self.controls.get_libcamera_controls()
        self.controls = Controls(self)

        return_code = self.camera.start(controls)
        if return_code < 0:
            msg = f"Camera did not start properly. ({return_code})"
            _log.error(msg)
            raise RuntimeError(msg)

        for request in self._make_requests():
            self.camera.queue_request(request)
        self.started = True
        _log.info("Camera started")

    def start(self, config=None) -> None:
        """
        Start the camera system running.

        Camera controls may be sent to the camera before it starts running.

        The following parameters may be supplied:

        config - if not None this is used to configure the camera. This is just a
            convenience so that you don't have to call configure explicitly.
        """
        if self.camera_config is None and config is None:
            config = "preview"
        if config is not None:
            self.configure(config)
        if self.camera_config is None:
            raise RuntimeError("Camera has not been configured")
        # By default we will create an event loop is there isn't one running already.
        if not self._preview:
            self.start_preview()
        self._start()

    def _stop(self) -> None:
        """Stop the camera.

        Only call this function directly from within the camera event
        loop, such as in a Qt application.
        """
        if self.started:
            self.stop_count += 1
            self.camera.stop()

            # Flush Requests from the event queue.
            # This is needed to prevent old completed Requests from showing
            # up when the camera is started the next time.
            self._cm.handle_request(self.camera_idx)
            self.started = False
            self._requests = deque()
            _log.info("Camera stopped")

    def stop(self) -> None:
        """Stop the camera."""
        if not self.started:
            _log.debug("Camera was not started")
            return
        if self.asynchronous:
            self._dispatch_no_request(self._stop).result()
        else:
            self._stop()

    def set_controls(self, controls) -> None:
        """Set camera controls. These will be delivered with the next request that gets submitted."""
        self.controls.set_controls(controls)

    def add_completed_request(self, request: CompletedRequest) -> None:
        self._requests.append(request)

    def process_requests(self) -> None:
        # Safe copy and pop off all requests
        requests = list(self._requests)
        for _ in requests:
            self._requests.popleft()

        self.frames += len(requests)

        req_idx = 0
        while len(self._task_deque) and (req_idx < len(requests)):
            task = self._task_deque.popleft()
            _log.debug(f"Begin LoopTask Execution: {task.call}")
            try:
                if task.needs_request:
                    req = requests[req_idx]
                    req_idx += 1
                    result = task.call(req)
                else:
                    result = task.call()
            except Exception as e:
                _log.warning(f"Error in LoopTask {task.call}: {e}")
                task.future.set_exception(e)
            task.future.set_result(result)
            _log.debug(f"End LoopTask Execution: {task.call}")

        for request in requests:
            for callback in self._request_callbacks:
                try:
                    callback(request)
                except Exception as e:
                    _log.error(f"Error in request callback ({callback}): {e}")

        for req in requests:
            req.release()

    def _dispatch_loop_tasks(self, *args: LoopTask) -> List[Future]:
        """The main thread should use this to dispatch a number of operations for the event
        loop to perform. The event loop will execute them in order, and return a list of
        futures which mature at the time the corresponding operation completes.
        """
        self._task_deque.extend(args)
        return [task.future for task in args]

    def _dispatch_with_temporary_mode(self, loop_task: LoopTask, config) -> Future:
        previous_config = self.camera_config
        futures = self._dispatch_loop_tasks(
            LoopTask.without_request(self._switch_mode, config),
            loop_task,
            LoopTask.without_request(self._switch_mode, previous_config),
        )
        return futures[1]

    def _capture_file(
        self, name, file_output, format, request: CompletedRequest
    ) -> dict:
        request.save(name, file_output, format=format)
        return request.get_metadata()

    def capture_file_async(
        self,
        file_output,
        name: str = "main",
        format=None,
    ) -> Future[dict]:
        return self._dispatch_loop_tasks(
            LoopTask.with_request(self._capture_file, name, file_output, format)
        )[0]

    def capture_file(
        self,
        file_output,
        name: str = "main",
        format=None,
    ) -> dict:
        """Capture an image to a file in the current camera mode.

        Return the metadata for the frame captured.
        """
        return self.capture_file_async(file_output, name, format).result()

    def _switch_mode(self, camera_config):
        self._stop()
        self._configure(camera_config)
        self._start()
        return self.camera_config

    def switch_mode(self, camera_config):
        """Switch the camera into another mode given by the camera_config."""
        return self._dispatch_loop_tasks(
            LoopTask.without_request(self._switch_mode, camera_config)
        )[0].result()

    def switch_mode_and_capture_file(
        self,
        camera_config,
        file_output,
        name="main",
        format=None,
    ):
        """Switch the camera into a new (capture) mode, capture an image to file, then return
        back to the initial camera mode.
        """
        return self._dispatch_with_temporary_mode(
            LoopTask.with_request(self._capture_file, name, file_output, format),
            camera_config,
        ).result()

    def _capture_request(self, request: CompletedRequest):
        request.acquire()
        return request

    def capture_request(self):
        """Fetch the next completed request from the camera system. You will be holding a
        reference to this request so you must release it again to return it to the camera system.
        """
        return self._dispatch_loop_tasks(LoopTask.with_request(self._capture_request))[
            0
        ].result()

    def switch_mode_capture_request_and_stop(self, camera_config):
        """Switch the camera into a new (capture) mode, capture a request in the new mode and then stop the camera."""
        futures = self._dispatch_loop_tasks(
            LoopTask.without_request(self._switch_mode, camera_config),
            LoopTask.with_request(self._capture_request),
            LoopTask.without_request(self._stop),
        )
        return futures[1].result()

    def _capture_metadata(self, request: CompletedRequest):
        return request.get_metadata()

    def capture_metadata(self) -> dict:
        """Fetch the metadata from the next camera frame."""
        return self.capture_metadata_async().result()

    def capture_metadata_async(self) -> Future:
        return self._dispatch_loop_tasks(LoopTask.with_request(self._capture_metadata))[
            0
        ]

    def _capture_buffer(self, name: str, request: CompletedRequest):
        return request.make_buffer(name)

    def capture_buffer(self, name="main"):
        """Make a 1d numpy array from the next frame in the named stream."""
        return self._dispatch_loop_tasks(LoopTask.with_request(self._capture_buffer))[
            0
        ].result()

    def _capture_buffers_and_metadata(
        self, names: List[str], request: CompletedRequest
    ) -> Tuple[List[np.ndarray], dict]:
        return ([request.make_buffer(name) for name in names], request.get_metadata())

    def capture_buffers(self, names=["main"]):
        """Make a 1d numpy array from the next frame for each of the named streams."""
        return self._dispatch_loop_tasks(
            LoopTask.with_request(self._capture_buffers_and_metadata, names)
        )[0].result()

    def switch_mode_and_capture_buffer(self, camera_config, name="main"):
        """Switch the camera into a new (capture) mode, capture the first buffer, then return
        back to the initial camera mode.
        """
        return self._dispatch_with_temporary_mode(
            LoopTask.with_request(self._capture_buffer, name), camera_config
        ).result()

    def switch_mode_and_capture_buffers(self, camera_config, names=["main"]):
        """Switch the camera into a new (capture) mode, capture the first buffers, then return
        back to the initial camera mode.
        """
        return self._dispatch_with_temporary_mode(
            LoopTask.with_request(self._capture_buffers_and_metadata, names),
            camera_config,
        ).result()

    def _capture_array(self, name, request: CompletedRequest):
        return request.make_array(name)

    def capture_array(self, name="main"):
        """Make a 2d image from the next frame in the named stream."""
        return self._dispatch_loop_tasks(
            LoopTask.with_request(self._capture_array, name)
        )[0].result()

    def _capture_arrays_and_metadata(
        self, names, request: CompletedRequest
    ) -> Tuple[List[np.ndarray], Dict[str, Any]]:
        return ([request.make_array(name) for name in names], request.get_metadata())

    def capture_arrays(self, names=["main"]):
        """Make 2d image arrays from the next frames in the named streams."""
        return self._dispatch_loop_tasks(
            LoopTask.with_request(self._capture_arrays_and_metadata, names)
        )[0].result()

    def switch_mode_and_capture_array(self, camera_config, name="main"):
        """Switch the camera into a new (capture) mode, capture the image array data, then return
        back to the initial camera mode."""
        return self._dispatch_with_temporary_mode(
            LoopTask.with_request(self._capture_array, name), camera_config
        ).result()

    def switch_mode_and_capture_arrays(self, camera_config, names=["main"]):
        """Switch the camera into a new (capture) mode, capture the image arrays, then return
        back to the initial camera mode."""
        return self._dispatch_with_temporary_mode(
            LoopTask.with_request(self._capture_arrays_and_metadata, names),
            camera_config,
        ).result()

    def _capture_image(self, name: str, request: CompletedRequest) -> Image:
        return request.make_image(name)

    def capture_image(self, name: str = "main") -> Image:
        """Make a PIL image from the next frame in the named stream.

        :param name: Stream name, defaults to "main"
        :type name: str, optional
        :param wait: Wait for the event loop to finish an operation and signal us, defaults to True
        :type wait: bool, optional
        :param signal_function: Callback, defaults to None
        :type signal_function: function, optional
        :return: PIL Image
        :rtype: Image
        """
        return self._dispatch_loop_tasks(
            LoopTask.with_request(self._capture_image, name)
        )[0].result()

    def switch_mode_and_capture_image(self, camera_config, name: str = "main") -> Image:
        """Switch the camera into a new (capture) mode, capture the image, then return
        back to the initial camera mode.
        """
        return self._dispatch_with_temporary_mode(
            LoopTask.with_request(self._capture_image, name), camera_config
        ).result()
