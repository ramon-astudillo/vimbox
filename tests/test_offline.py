import os
import copy
import sys
import shutil
from vimbox.__main__ import main
from vimbox.local import (
    load_config,
    get_local_file,
    write_config,
    CONFIG_FILE,
)

# Name of the folder where we carry on the test
UNIT_TEST_FOLDER = '/14s52fr34G2R3tH42341/'


def read_file(file_path):
    with open(file_path) as fid:
        return fid.read()


FAKE_REMOTE_STORAGE = "%s/.fake_remote/" % \
    os.path.realpath(os.path.dirname(__file__))


def get_remote_path(remote_file):
    return "%s/%s" % (FAKE_REMOTE_STORAGE, remote_file)


def read_remote_content(remote_file):
    true_path = get_remote_path(remote_file)
    #with codecs.open(true_path, 'r', 'utf-8') as fid:
    with open(true_path, 'r') as fid:
        text = fid.read()
    return text


def test_main(config):

    # Get initial config, set backend to fake
    # FIXME: If this dies it will leave the backend set to fake
    config['backend_name'] = 'fake-offline'


def reset_environment(original_config=None):
    """
    - Remove folder simulating storage in remote
    - Remove folder in the local vimbox cache (THIS IS THE ACTUAL CACHE)
    - keep original config to restore it later
    """
    fake_remote_storage = get_remote_path(UNIT_TEST_FOLDER)
    local_storage = get_local_file(UNIT_TEST_FOLDER)
    if os.path.isdir(fake_remote_storage):
        shutil.rmtree(fake_remote_storage)
    if os.path.isdir(local_storage):
        shutil.rmtree(local_storage)
    if original_config:
        print("Restored config before tests")
        write_config(CONFIG_FILE, original_config)
    else:
        return load_config()


if __name__ == '__main__':

    original_config = reset_environment()
    test_main(copy.deepcopy(original_config))
    reset_environment(original_config)

    try:

        pass

    except Exception as exception:
        # Ensure we restore the original config
        reset_environment(original_config)
        # Reraise error
        t, v, tb = sys.exc_info()
        raise t, v, tb
