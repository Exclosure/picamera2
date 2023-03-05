#!/usr/bin/python3
"""scicamera main classes"""
from __future__ import annotations

import logging
import selectors
import threading
from collections import deque
from dataclasses import replace
from functools import partial
from typing import Dict, List

import libcamera

import scicamera.formats as formats
from scicamera.actions import RequestMachinery
from scicamera.configuration import CameraConfig, StreamConfig
from scicamera.controls import Controls
from scicamera.info import CameraInfo
from scicamera.lc_helpers import errno_handle, lc_unpack, lc_unpack_controls
from scicamera.preview import NullPreview
from scicamera.request import CompletedRequest, LoopTask
from scicamera.sensor_format import SensorFormat
from scicamera.tuning import TuningContext

_log = logging.getLogger(__name__)


class CameraManager:
    cameras: Dict[int, Camera]

    _instance: CameraManager = None

    @classmethod
    def singleton(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.running = False
        self.cameras = {}
        self._lock = threading.Lock()
        self.cms = libcamera.CameraManager.singleton()

    def n_cameras_attached(self):
        return len(self.cms.cameras)

    def get_camera(self, idx: int):
        """Get the (lc) camera with the given index"""
        return self.cms.cameras[idx]

    def setup(self):
        self.thread = threading.Thread(target=self.listen, daemon=True)
        self.running = True
        self.thread.start()

    def close_all(self) -> int:
        n_closed = 0
        ids_to_close = list(self.cameras.keys())
        for idx in ids_to_close:
            # FIXME(meawoppl) - this calls back into self.cleanup()
            self.cameras[idx].close()
            n_closed += 1
        return n_closed

    def add(self, index: int, camera: Camera):
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

    def listen(self):
        sel = selectors.DefaultSelector()
        sel.register(self.cms.event_fd, selectors.EVENT_READ, self.handle_request)

        while self.running:
            events = sel.select(0.05)
            for key, _ in events:
                callback = key.data
                callback()

        sel.unregister(self.cms.event_fd)

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
                    camera_inst = self.cameras[req.cookie]
                    cleanup_call = partial(
                        camera_inst.recycle_request, camera_inst.stop_count, req
                    )
                    self.cameras[req.cookie].add_completed_request(
                        CompletedRequest(
                            req,
                            replace(camera_inst.camera_config),
                            camera_inst.stream_map,
                            cleanup_call,
                        )
                    )


class Camera(RequestMachinery):
    """Welcome to the Camera class."""

    def __init__(self, camera_num: int = 0, tuning=None):
        """Initialise camera system and open the camera for use.

        :param camera_num: Camera index, defaults to 0
        :type camera_num: int, optional
        :param tuning: Tuning filename, defaults to None
        :type tuning: str, optional
        :raises RuntimeError: Init didn't complete
        """
        super().__init__()
        self._cm = CameraManager.singleton()

        self._cm.add(camera_num, self)
        self.camera_idx = camera_num
        self._reset_flags()

        with TuningContext(tuning):
            self._open_camera()

    def _reset_flags(self) -> None:
        self.camera = None
        self.is_open = False
        self.camera_ctrl_info = {}
        self._preview = None
        self.camera_config = None
        self.streams = None
        self.stream_map = None
        self.started = False
        self.stop_count = 0
        self.camera_properties_ = {}
        self.controls = Controls(self)
        self.sensor_modes_ = None

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

    def __del__(self):
        """Without this libcamera will complain if we shut down without closing the camera."""
        if self.is_open:
            _log.warning(f"__del__ call responsible for cleanup of {self}")
            self.close()

    def _initialize_camera(self) -> None:
        """Initialize camera

        :raises RuntimeError: Failure to initialize camera
        """
        CameraInfo.requires_camera()

        self.camera = self._cm.get_camera(self.camera_idx)
        if self.camera is None:
            message = "Initialization failed."
            _log.error(message)
            raise RuntimeError(message)

        self.__identify_camera()
        self.camera_ctrl_info = lc_unpack_controls(self.camera.controls)
        self.camera_properties_ = lc_unpack(self.camera.properties)

        # The next two lines could be placed elsewhere?
        self.sensor_resolution = self.camera_properties_["PixelArraySize"]
        self.sensor_format = str(
            self.camera.generate_configuration([libcamera.StreamRole.Raw])
            .at(0)
            .pixel_format
        )

        _log.info("Initialization successful.")

    def __identify_camera(self):
        # TODO(meawoppl) make this a helper on the camera_manager
        for idx, address in enumerate(self._cm.cms.cameras):
            if address == self.camera:
                self.camera_idx = idx
                break

    def _open_camera(self) -> None:
        """Tries to open camera

        :raises RuntimeError: Failed to setup camera
        """
        self._initialize_camera()

        acq_code = self.camera.acquire()
        errno_handle(acq_code, "camera.acquire()")

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
                temp_config = CameraConfig.for_preview(
                    camera=self, raw={"format": str(pix), "size": cam_mode["size"]}
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
        code = self.camera.release()
        errno_handle(code, "camera.release()")

        self._cm.cleanup(self.camera_idx)
        self.is_open = False
        self.streams = None
        self.stream_map = None
        self.camera = None
        self.camera_ctrl_info = None
        self.camera_config = None
        self._preview_configuration = None
        self.allocator = None
        _log.info("Camera closed successfully.")

    def recycle_request(self, stop_count: int, request: libcamera.Request) -> None:
        """Recycle a request.

        :param request: request
        :type request: libcamera.Request
        """
        if not self.camera:
            _log.warning("Can't recycle request, camera not open")
            return

        if stop_count != self.stop_count:
            _log.warning("Can't recycle request, stop count mismatch")
            return

        request.reuse()

        # This is where controls on the camera get updated
        # TODO(meawoppl) - attach a future to he request.cookie
        # so that we can mature the future when the controls are set
        controls = self.controls.get_libcamera_controls()
        for id, value in controls.items():
            request.set_control(id, value)
        self.controls = Controls(self)

        code = self.camera.queue_request(request)
        errno_handle(code, f"camera.queue_request({request})")

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

    def _config_opts(self, config: dict | CameraConfig) -> CameraConfig:
        if isinstance(config, CameraConfig):
            return config

        if isinstance(config, dict):
            _log.warning("Using old-style camera config, please update")
            config = config.copy()
            return CameraConfig(camera=self, **config)

        raise RuntimeError(
            f"Don't know how to make a config from {config} ({type(config)})"
        )

    def configure(self, config: dict | CameraConfig) -> None:
        """Configure the camera system with the given configuration.

        :param camera_config: Configuration, defaults to the 'preview' configuration
        :type camera_config: dict, string or CameraConfiguration, optional
        :raises RuntimeError: Failed to configure
        """
        if self.started:
            raise RuntimeError("Camera must be stopped before configuring")
        camera_config = self._config_opts(config)

        # Mark ourselves as unconfigured.
        self.camera_config = None

        # Check the config and turn it into a libcamera config.
        camera_config.apply(self.camera)
        self.stream_map = camera_config.get_stream_map()

        # Update the controls and properties list as some of the values may have changed.
        self.camera_ctrl_info = lc_unpack_controls(self.camera.controls)
        self.camera_properties_ = lc_unpack(self.camera.properties)

        # Allocate all the frame buffers.
        self.streams = [
            stream_config.stream for stream_config in camera_config.libcamera_config
        ]

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
        self.camera_config = camera_config

        # Set the controls directly so as to overwrite whatever is there.
        self.controls.set_controls(self.camera_config.controls)

    def camera_configuration(self) -> CameraConfig:
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

        code = self.camera.start(controls)
        errno_handle(code, "camera.start()")

        for request in self._make_requests():
            self.camera.queue_request(request)
        self.started = True
        _log.info("Camera started")

    def start(self) -> None:
        """
        Start the camera system running.

        Camera controls may be sent to the camera before it starts running.

        The following parameters may be supplied:

        config - if not None this is used to configure the camera. This is just a
            convenience so that you don't have to call configure explicitly.
        """
        if self.camera_config is None:
            _log.warning("Camera has not been configured, using preview config")
            self.configure(CameraConfig.for_preview(self))
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
            code = self.camera.stop()
            errno_handle(code, "camera.stop()")

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
            self._dispatch_loop_tasks(LoopTask.without_request(self._stop))[0].result()
        else:
            self._stop()

    def set_controls(self, controls) -> None:
        """Set camera controls. These will be delivered with the next request that gets submitted."""
        self.controls.set_controls(controls)
