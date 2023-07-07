import pytest

from scicamera import Camera, CameraConfig


def _skip_if_no_raw(camera: Camera):
    if camera.sensor_format == "MJPEG":
        pytest.skip("Skipping raw test for MJPEG camera")


def test_capture_raw():
    with Camera() as camera:
        _skip_if_no_raw(camera)

        camera.start_preview()

        preview_config = CameraConfig.for_preview(camera)
        preview_config.enable_raw()
        print(preview_config)
        width, height = preview_config.raw.size

        camera.configure(preview_config)
        assert camera.camera_configuration().get_stream_config("raw") is not None

        camera.start()
        camera.discard_frames(4).result()
        raw = camera.capture_array("raw").result()

        if camera.info.model == "imx477":
            assert camera.sensor_format == "SBGGR12_CSI2P"

        if camera.info.model == "imx219":
            assert camera.sensor_format == "SBGGR10_CSI2P"

        assert raw.shape == (height, width)
