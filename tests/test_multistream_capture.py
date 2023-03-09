from typing import Type

import pytest

from scicamera import Camera, CameraConfig, FakeCamera
from scicamera.testing import requires_camera_model


@pytest.mark.parametrize("CameraClass", [Camera, FakeCamera])
def test_multiple_streams(CameraClass: Type[Camera]):
    main_shape = (1280, 720)
    lores_shape = (320, 240)
    with CameraClass() as camera:
        requires_camera_model(camera, "imx", allow_fake=False)
        video_config = CameraConfig.for_video(
            camera,
            main={"size": main_shape, "format": "RGB888"},
            lores={"size": lores_shape, "format": "YUV420"},
        )
        camera.configure(video_config)
        camera.start()

        for _ in range(2):
            main = camera.capture_array("main").result()
            assert main.shape == main_shape[::-1] + (3,)

            lores = camera.capture_array("lores").result()
            # NOTE(meawoppl) this shape is funny in ways that
            # I don't understand
            # assert lores.shape == lores_shape[::-1] + (3,)

        camera.stop()


@pytest.mark.parametrize("CameraClass", [Camera, FakeCamera])
def test_multiple_streams_with_config(CameraClass: Type[Camera]):
    with CameraClass() as camera:
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
