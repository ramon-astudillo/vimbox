import os
import copy
import sys
import shutil
from vimbox.local import (
    load_config,
    get_local_file,
    write_config,
    CONFIG_FILE,
)
from vimbox.remote.dropbox_backend import StorageBackEnd


# Name of the folder where we carry on the test
# Chosen by fair dice roll. Guaranteed to be random.
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
    '''
    Test StorageBackEnd primitives
    '''

    assert UNIT_TEST_FOLDER == '/14s52fr34G2R3tH42341/', \
        "CHANGING INTEGRATION TEST FOLDER CAN LEAD TO DATA LOSS"
    assert UNIT_TEST_FOLDER[-1] == '/', "Folder paths end in /"

    # Get initial config, set backend to fake
    # FIXME: If this dies it will leave the backend set to fake
    config['backend_name'] = 'dropbox'
    assert 'DROPBOX_TOKEN' in config, "DROPBOX_TOKEN is needed in config"

    TMP_FILE = '%splain' % UNIT_TEST_FOLDER
    TMP_CONTENT = 'This is some text'
    TMP_FILE2 = '%splain2' % UNIT_TEST_FOLDER

    client = StorageBackEnd(config['DROPBOX_TOKEN'])

    client.get_user_account()
    # Create
    client.files_upload(TMP_CONTENT, TMP_FILE)

    # Check existance file
    is_file, status = client.is_file(TMP_FILE)
    assert status == 'online', "Status not online on is_file"
    assert is_file, "Dropbox file creation failed"

    # Check existance folder
    is_file, status = client.is_file(UNIT_TEST_FOLDER[:-1])
    assert status == 'online', "Status not online on is_file"
    assert not is_file, "Dropbox can not see folder in remote"

    # Check content
    remote_content, status = client.file_download(TMP_FILE)
    assert status == 'online', "Status not online on file_download"
    assert TMP_CONTENT == remote_content, "Retrieval of remote content failed"

    # List folders does not die
    result, status = client.list_folders(UNIT_TEST_FOLDER[:-1])
    assert status == 'online', "Status not online on list_folders"

    # Move
    client.files_copy(TMP_FILE, TMP_FILE2)
    client.files_delete(TMP_FILE)

    # Check non existance file
    is_file, status = client.is_file(TMP_FILE)
    assert status == 'api-error', "File removal failed"

    # Clean-up
    client.files_delete(UNIT_TEST_FOLDER[:-1])

    # Check existance folder
    is_file, status = client.is_file(UNIT_TEST_FOLDER[:-1])
    assert status == 'api-error', "Folder removal failed"


def reset_environment(original_config=None):
    """
    - Remove folder simulating storage in remote
    - Remove folder in the local vimbox cache (THIS IS THE ACTUAL CACHE)
    - keep original config to restore it later
    """
    local_storage = get_local_file(UNIT_TEST_FOLDER)
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
        t, v, tb = sys.exc_info()
        raise t, v, tb
