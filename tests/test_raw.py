# Configure a raw stream and capture an image from it.
import os
import tempfile
from logging import getLogger

import numpy as np
import pytest
from PIL import Image

from scicamera import Camera, CameraConfig
from scicamera.sensor_format import SensorFormat

_log = getLogger(__name__)


def _skip_if_no_raw(camera: Camera):
    if camera.sensor_format == "MJPEG":
        pytest.skip("Skipping raw test for MJPEG camera")


def test_capture_raw():
    with Camera() as camera:
        _skip_if_no_raw(camera)

        camera.start_preview()

        preview_config = CameraConfig.for_preview(
            camera,
            raw={"size": camera.sensor_resolution, "format": camera.sensor_format},
        )
        print(preview_config)


        camera.configure(preview_config)

        assert camera.camera_configuration().get_stream_config("raw") is not None

        camera.start()
        camera.discard_frames(4).result()
        raw = camera.capture_array("raw").result()
        print(raw.shape)
        assert raw.shape == camera.sensor_resolution


def test_raw_stacking():
    exposure_time = 60000
    num_frames = 6

    # Configure an unpacked raw format as these are easier to add.
    with Camera() as camera:
        _skip_if_no_raw(camera)

        raw_format = SensorFormat(camera.sensor_format)
        raw_format.packing = None
        config = CameraConfig.for_still(
            camera, raw={"format": raw_format.format}, buffer_count=2
        )
        camera.configure(config)
        images = []
        camera.set_controls(
            {"ExposureTime": exposure_time // num_frames, "AnalogueGain": 1.0}
        )
        camera.start()

        # The raw images can be added directly using 2-byte pixels.
        for i in range(num_frames):
            _log.info("Captureing frame %s", i + 1)
            images.append(camera.capture_array("raw").result().view(np.uint16))
        metadata = camera.capture_metadata().result()

        accumulated = images.pop(0).astype(int)
        for image in images:
            accumulated += image

        # Fix the black level, and convert back to uint8 form for saving as a DNG.
        black_level = metadata["SensorBlackLevels"][0] / 2 ** (
            16 - raw_format.bit_depth
        )
        accumulated -= (num_frames - 1) * int(black_level)
        accumulated = accumulated.clip(0, 2**raw_format.bit_depth - 1).astype(
            np.uint16
        )
        accumulated = accumulated.view(np.uint8)
        metadata["ExposureTime"] = exposure_time

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "accumulated.jpg")
            Image.fromarray(accumulated).save(path)
            assert os.path.isfile(path)
