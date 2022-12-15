import os
import pytest
import subprocess
import sys

this_folder, this_file = os.path.split(__file__)

test_file_names = [name for name in os.listdir(this_folder) if name.endswith('.py')]
test_file_names.remove(this_file)

def forward_subprocess_output(e: subprocess.CalledProcessError):
    print(e.stdout.decode("utf-8"), end='')
    print(e.stderr.decode("utf-8"), end='', file=sys.stderr)

@pytest.mark.parametrize('test_file_name', test_file_names)
def test_file(test_file_name):
    try:
        subprocess.run(['python', test_file_name], cwd=this_folder, timeout=20, capture_output=True, check=True).check_returncode()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        forward_subprocess_output(e)
        raise 
