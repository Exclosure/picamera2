"""NOTE(meawoppl) This is a pytest script that runs the old tests.

Do not add new tests here, instead add them to the new test suite.
Follow patterns found in `/tests/test_*.py` to maximize your joy.
"""
import os
import subprocess
import sys

import pytest

this_folder, this_file = os.path.split(__file__)
old_test_folder = os.path.join(this_folder, "old")

test_file_names = list(
    name for name in os.listdir(old_test_folder) if name.endswith(".py")
)
test_file_names.sort()


def forward_subprocess_output(e: subprocess.CalledProcessError):
    if e.stdout:
        print(e.stdout.decode("utf-8"), end="")
    if e.stderr:
        print(e.stderr.decode("utf-8"), end="", file=sys.stderr)


KNOWN_XFAIL = set(
    [
        "capture_circular.py",
        "drm_multiple_test.py",
        "raw.py",
        "stack_raw.py",
    ]
)


def test_xfail_list():
    for xfail_name in KNOWN_XFAIL:
        assert (
            xfail_name in test_file_names
        ), f"XFAIL {xfail_name} not in test_file_names (remove it from KNOWN_XFAIL)"


@pytest.mark.parametrize("test_file_name", test_file_names)
def test_file(test_file_name):
    success = False
    process_env = os.environ.copy()
    process_env["LIBCAMERA_LOG_LEVELS"] = "*:DEBUG"

    try:
        subprocess.run(
            ["python", test_file_name],
            cwd=old_test_folder,
            env=process_env,
            timeout=20,
            capture_output=True,
            check=True,
        ).check_returncode()
        success = True
    except subprocess.TimeoutExpired as e:
        forward_subprocess_output(e)
    except subprocess.CalledProcessError as e:
        forward_subprocess_output(e)

    # Special handle the XFAIL tests
    if test_file_name in KNOWN_XFAIL:
        if success:
            pytest.fail(
                f"Test passed unexpectedly (needs removal from XFAIL list): {test_file_name}",
                pytrace=False,
            )
        else:
            if test_file_name in KNOWN_XFAIL:
                pytest.xfail(f"Known broken: {test_file_name}")

    if not success:
        pytest.fail(f"Test failed: {test_file_name}", pytrace=False)
