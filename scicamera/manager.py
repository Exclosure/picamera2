from __future__ import annotations
import threading
import libcamera
from typing import Dict, TYPE_CHECKING
from dataclasses import replace
from functools import partial
from scicamera.request import CompletedRequest
from scicamera.misc import make_completed_thread
import selectors

from logging import getLogger

_log = getLogger(__name__)

if TYPE_CHECKING:
    from scicamera.camera import Camera
    

class CameraManager:
    _instance: CameraManager = None

    @classmethod
    def singleton(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    index_to_scicam: Dict[int, Camera]

    def __init__(self):
        self.index_to_scicam = {}
        self._lock = threading.Lock()
        self.cms = libcamera.CameraManager.singleton()
        self._thread = make_completed_thread()

    def get_camera(self, index: int, camera: Camera):
        """Get the (lc) camera with the given index
        
        This additionally register callbacks to be made to
        the ``Camera`` instance when the camera is ready
        """
        lc_camera = self.cms.cameras[index]
        _log.info("Got camera %s", lc_camera)
        with self._lock:
            self.index_to_scicam[index] = camera
            if not self._thread.is_alive():
                self._thread = threading.Thread(target=self.listen, daemon=True)
                self._thread.start()
                _log.info("Started camera manager thread")
        return lc_camera       

    def cleanup(self, index: int):
        with self._lock:
            del self.index_to_scicam[index]
            if self.index_to_scicam == {}:
                self._thread.join()
                _log.info("Joined camera manager thread")

    def listen(self):
        sel = selectors.DefaultSelector()
        sel.register(self.cms.event_fd, selectors.EVENT_READ)

        while self.index_to_scicam:
            for _ in sel.select(0.2):
                self.handle_request()

        sel.unregister(self.cms.event_fd)

    def handle_request(self, flushid=None):
        """Handle requests"""
        with self._lock:
            for req in self.cms.get_ready_requests():
                if (
                    req.status == libcamera.Request.Status.Complete
                    and req.cookie != flushid
                ):
                    camera_inst = self.index_to_scicam[req.cookie]
                    cleanup_call = partial(
                        camera_inst.recycle_request, camera_inst.stop_count, req
                    )
                    self.index_to_scicam[req.cookie].add_completed_request(
                        CompletedRequest(
                            req,
                            replace(camera_inst.camera_config),
                            camera_inst.stream_map,
                            cleanup_call,
                        )
                    )
