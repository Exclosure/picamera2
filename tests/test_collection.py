import os
import subprocess
import sys

import pytest
import numpy as np

from picamera2 import Picamera2
from picamera2.picamera2 import CameraManager

this_folder, this_file = os.path.split(__file__)

test_file_names = [name for name in os.listdir(this_folder) if name.endswith(".py")]
test_file_names.remove(this_file)
test_file_names.sort()


def forward_subprocess_output(e: subprocess.CalledProcessError):
    if e.stdout:
        print(e.stdout.decode("utf-8"), end="")
    if e.stderr:
        print(e.stderr.decode("utf-8"), end="", file=sys.stderr)


# def test_init():
#     for i in range(3):
#         cam = Picamera2()
#         cam.close()



# def test_init_acquire():
#     cam = Picamera2()
#     cam.start()
#     array = cam.capture_array()
#     assert isintance(array, np.ndarray)
#     cam.stop()
#     cam.close()


# @pytest.mark.xfail(reason="Not validated to be working")
@pytest.mark.parametrize("test_file_name", test_file_names)
def test_file(test_file_name):
    print(sys.path)
    success = False
    try:
        subprocess.run(
            ["python", test_file_name],
            cwd=this_folder,
            timeout=60,
            capture_output=True,
            check=True,
        ).check_returncode()
        success = True
    except subprocess.TimeoutExpired as e:
        forward_subprocess_output(e)
    except subprocess.CalledProcessError as e:
        forward_subprocess_output(e)

    if not success:
        pytest.fail(f"Test failed: {test_file_name}", pytrace=False)
