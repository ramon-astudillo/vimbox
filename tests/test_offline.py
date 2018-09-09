import os
import sys
import copy
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
    with open(true_path, 'r') as fid:
        text = fid.read()
    return text


def test_main(config):

    # Get initial config, set backend to fake
    # FIXME: If this dies it will leave the backend set to fake
    config['backend_name'] = 'fake-offline'

    TMP_FILE = '%splain' % UNIT_TEST_FOLDER
    TMP_CONTENT = 'This is some text'
    TMP_FILE2 = '%splain2' % UNIT_TEST_FOLDER

    # Files in this computer
    local_file = get_local_file(TMP_FILE, config=config)

    # NORMAL FILE
    read_config = load_config()
    # Creation
    main(['-f', TMP_FILE, TMP_CONTENT], config=config)
    # Check a local copy was created (if intended)
    assert os.path.isfile(local_file), \
        "Creation of local file %s failed" % local_file
    # Check if the folder was added to the cache
    read_config = load_config()
    dirname = "%s/" % os.path.dirname(TMP_FILE)
    assert dirname in read_config['cache'], "Register in cache failed"

    # Move file

    # This tests both copy and remove
    main(['mv', TMP_FILE, TMP_FILE2], config=config)
    # Check local file was not removed
    assert os.path.isfile(local_file), \
        "local file %s can not be removed while offline" % local_file
    local_file2 = get_local_file(TMP_FILE2, config=config)
    assert not os.path.isfile(local_file2), \
        "local file %s can not be created by copy while offline" % local_file

    # ENCRYPTED FILE CREATION
    # TODO: This returns with exit which will skip restablishing of config
#     FAKE_FILE_ENCRYPTED = '/14s52fr34G2R3tH42341/encrypted'
#     FAKE_SECRET_CONTENT = "This is some encrypted text"
#     PASSWORD = 'dummy'
#     #
#     # Creating ecrypted files while offline makes no sense
#     main(
#         ['-e', FAKE_FILE_ENCRYPTED, FAKE_SECRET_CONTENT],
#         config=config,
#         password=PASSWORD
#     )
#     local_encrypted = get_local_file(FAKE_FILE_ENCRYPTED, config=config)
#     assert not os.path.isfile(local_file2), \
#         "Should not create local file while offline if encrypted"


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

    try:
        original_config = reset_environment()
        test_main(copy.deepcopy(original_config))
        reset_environment(original_config)

    except Exception as exception:
        # Ensure we restore the original config
        reset_environment(original_config)
        # Reraise error
        if sys.version_info[0] > 2:
            raise exception.with_traceback(sys.exc_info()[2])
        else:
            t, v, tb = sys.exc_info()
            raise(t, v, tb)
