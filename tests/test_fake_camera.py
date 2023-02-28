import time

import numpy as np
import pytest
from PIL import Image

from scicamera.fake import FakeCamera
from scicamera.testing import mature_after_frames_or_timeout


@pytest.fixture
def camera():
    camera = FakeCamera()
    camera.start()
    yield camera
    camera.stop()
    camera.close()


def test_fake_camera_init():
    FakeCamera()


def test_fake_camera_run_internals():
    camera = FakeCamera()
    camera.start()

    mature_after_frames_or_timeout(camera, 10, 1)

    camera.stop()
    camera.close()

def test_fake_image_plausible(show=False):
    camera = FakeCamera()
    camera.start()
    img = camera.capture_image().result(timeout=0.2)
    if show:
        img.show()

    img_array = camera.capture_array().result(timeout=0.2)
    # First row is red
    assert np.all(img_array[:, 0, 0] == 255)

    # Middle row is green
    assert np.all(img_array[:, img_array.shape[1]// 2, 1] == 255)

    # Last row is blue
    assert np.all(img_array[:, -1, 2] == 255)

    camera.stop()

def test_fake_camera_makes_images():
    camera = FakeCamera()

    capt = camera.capture_array()
    time.sleep(0.1)
    assert not capt.done()

    camera.start()

    camera.capture_array().result(timeout=0.5)
    camera.capture_metadata().result()
    a = [frame.result for frame in camera.capture_serial_frames(3)]
    camera.capture_buffer()

    camera.stop()
    camera.close()


def test_fake_metadata(camera: FakeCamera):
    metadata = camera.capture_metadata().result(timeout=0.2)
    assert isinstance(metadata, dict)


def test_fake_array(camera: FakeCamera):
    array = camera.capture_array().result(timeout=0.2)
    assert isinstance(array, np.ndarray)


def test_fake_buffer(camera: FakeCamera):
    buffer = camera.capture_buffer().result(timeout=0.2)
    assert isinstance(buffer, np.ndarray)


def test_fake_image(camera: FakeCamera):
    image = camera.capture_image().result(timeout=0.2)
    assert isinstance(image, Image.Image)
