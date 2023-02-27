from threading import Event, Thread
from typing import Any, Dict

import libcamera
import numpy as np

from scicamera.actions import RequestMachinery
from scicamera.configuration import CameraConfig, StreamConfig
from scicamera.request import CompletedRequest


def make_fake_image(shape: tuple):
    img = np.zeros(shape + (3,), dtype=np.uint8)
    w, h = shape
    img[:, 0 : w // 3, 0] = 255
    img[:, w // 3 : 2 * w // 3, 1] = 255
    img[:, 2 * w // 3 :, 2] = 255
    return img


class FakeCompletedRequest(CompletedRequest):
    def __init__(self, config: CameraConfig):
        self._config = config

    def acquire(self):
        pass

    def release(self):
        pass

    def get_config(self, name: str) -> Dict[str, Any]:
        """Fetch the configuration for the named stream."""
        return self._config

    def get_buffer(self, name: str) -> np.ndarray:
        """Make a 1d numpy array from the named stream's buffer."""
        size = self._config.get_config(name).size
        return make_fake_image(size).flatten()

    def get_metadata(self) -> Dict[str, Any]:
        """Fetch the metadata corresponding to this completed request."""
        return {}


class FakeCamera(RequestMachinery):
    def __init__(self) -> None:
        super().__init__()
        self._t = Thread(target=lambda: None, daemon=True)
        self._t.start()
        self._t.join()
        self._abort = Event()

        self.config = CameraConfig(
            self,
            "still",
            1,
            controls={},
            transform=libcamera.Transform(),
            color_space=libcamera.ColorSpace.Sycc(),
            main=StreamConfig((320, 240), format="BGR888", stride=320 * 3),
        )

    def _run(self):
        while not self._abort.wait(0.1):
            request = FakeCompletedRequest(self.config)
            self.add_completed_request(request)
            self.process_requests()

    def configure(self, config: CameraConfig) -> None:
        self.config = config

    def start(self) -> None:
        self._t = Thread(target=self._run, daemon=True)
        self._abort.clear()
        self._t.start()

    def stop(self) -> None:
        self._abort.set()
        self._t.join()

    def close(self) -> None:
        if self._t.is_alive():
            self.stop()
