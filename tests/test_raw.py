import pytest

from scicamera import Camera, CameraConfig


def _skip_if_no_raw(camera: Camera):
    if camera.sensor_format == "MJPEG":
        pytest.skip("Skipping raw test for MJPEG camera")


def test_capture_raw():
    with Camera() as camera:
        _skip_if_no_raw(camera)

        camera.start_preview()

        # Still config makes the main stream the rez of the sensor
        still_config = CameraConfig.for_still(camera)
        still_config.enable_raw()
        print(still_config)
        width, height = still_config.raw.size

        camera.configure(still_config)
        assert camera.camera_configuration().get_stream_config("raw") is not None

        camera.start()
        camera.discard_frames(4).result()
        raw = camera.capture_array("raw").result()

        if camera.info.model == "imx477":
            assert camera.sensor_format == "SBGGR12_CSI2P"

        if camera.info.model == "imx219":
            assert camera.sensor_format == "SBGGR10_CSI2P"

        print(camera.info.model)
        assert raw.shape == (height, width)
