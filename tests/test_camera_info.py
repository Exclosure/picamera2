from typing import Type

import pytest

from scicamera import Camera, FakeCamera
from scicamera.testing import requires_camera_model


@pytest.mark.parametrize("CameraClass", [Camera, FakeCamera])
def test_camera_info(CameraClass: Type[Camera]):
    with CameraClass() as camera:
        assert isinstance(camera.info.model, str)
        assert isinstance(camera.info.id, str)


def test_camera_skip():
    # FakeCamera is every camera model....
    camera = FakeCamera()
    requires_camera_model(camera, "XXX", allow_fake=True)


def test_fake_camera_skip():
    camera = FakeCamera()
    requires_camera_model(camera, "XXX", allow_fake=False)
    pytest.fail("Should be skipped.")


def test_camera_skip_fail():
    with Camera() as camera:
        requires_camera_model(camera, "XXX")
        pytest.fail("Should be skipped.")
