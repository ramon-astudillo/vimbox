import os
import copy
import sys
from vimbox.__main__ import main
from vimbox.crypto import get_path_hash
from vimbox.local import load_config, get_local_file
from tools import (
    get_remote_path,
    read_remote_content,
    reset_environment,
    UNIT_TEST_FOLDER
)
from vimbox.remote.dropbox_backend import StorageBackEnd

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
    if sys.version_info[0] > 2:
        # Encoding for Python3
        TMP_CONTENT = str.encode(TMP_CONTENT)
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
    if sys.version_info[0] > 2:
        # Encoding for Python3
        remote_content = str.encode(remote_content)
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



if __name__ == '__main__':

    try:
        original_config = reset_environment()
        test_main(copy.deepcopy(original_config))
        reset_environment(original_config, sucess=True)

    except Exception as exception:
        # Ensure we restore the original config
        reset_environment(original_config)
        # Reraise error
        if sys.version_info[0] > 2:
            raise exception.with_traceback(sys.exc_info()[2])
        else:
            t, v, tb = sys.exc_info()
            raise(t, v, tb)
