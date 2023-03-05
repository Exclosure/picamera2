import numpy as np

from scicamera import Camera, CameraConfig, FakeCamera

from typing import Type
import pytest

@pytest.mark.parametrize("CameraClass", [Camera, FakeCamera])
def test_multiple_streams(CameraClass: Type[Camera]):
    main_size = (1280, 720)
    lores_size = (320, 240)
    camera = Camera()
    video_config = CameraConfig.for_video(
        camera,
        main={"size": main_size, "format": "RGB888"},
        lores={"size": lores_size, "format": "YUV420"},
    )
    camera.configure(video_config)
    camera.start()

    for _ in range(2):
        cur = camera.capture_array("lores").result()
        assert cur.size == lores_size + (3,)

        main_array = camera.capture_array("main").result()
        assert main_array.size == main_size + (3,)

    camera.stop()

@pytest.mark.parametrize("CameraClass", [Camera, FakeCamera])
def test_multiple_streams_with_config(CameraClass: Type[Camera]):
    camera = CameraClass()
    camera.start_preview()

    preview_config = CameraConfig.for_preview(camera)
    camera.configure(preview_config)

    camera.start()
    camera.discard_frames(4)
    other_config = CameraConfig.for_preview(
        camera, main={"size": camera.sensor_resolution}, buffer_count=3
    )

    camera.switch_mode(other_config)
    camera.discard_frames(4).result()
    camera.stop()
    camera.close()
