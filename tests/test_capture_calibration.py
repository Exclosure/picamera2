from datetime import datetime
from typing import Type

import pytest

from scicamera import Camera, CameraConfig
from scicamera.fake import FakeCamera
from scicamera.timing import calibrate_camera_offset


@pytest.mark.parametrize("CameraClass", [Camera, FakeCamera])
def test_capture_time_calibration(CameraClass: Type[Camera]):
    camera = CameraClass()
    video_config = CameraConfig.for_video(camera)
    camera.configure(video_config)

    camera.start()
    offset = calibrate_camera_offset(camera, 20)

    sensor_timestamp = camera.capture_metadata().result()["SensorTimestamp"]
    print(f"SensorTimestamp: {sensor_timestamp} ({len(str(sensor_timestamp))})")
    print(f"Offset: {offset} ({len(str(offset))}))")
    exposure_time = datetime.fromtimestamp((sensor_timestamp + offset) / 1e9)
    time_offset = abs(exposure_time - datetime.now()).total_seconds()

    assert time_offset < 1, time_offset

    camera.stop()
    camera.close()
