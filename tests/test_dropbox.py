import copy
import sys
from vimbox.__main__ import main
from vimbox.crypto import get_path_hash
from vimbox.local import load_config, get_local_file
from tools import (
    get_remote_path,
    read_remote_content,
    start_environment,
    reset_environment,
    REMOTE_UNIT_TEST_FOLDER,
    green
)
from vimbox.remote.dropbox_backend import StorageBackEnd

def test_main():
    '''
    Test StorageBackEnd primitives
    '''

    assert REMOTE_UNIT_TEST_FOLDER == '/14s52fr34G2R3tH42341/', \
        "CHANGING INTEGRATION TEST FOLDER CAN LEAD TO DATA LOSS"
    assert REMOTE_UNIT_TEST_FOLDER[-1] == '/', "Folder paths end in /"

    TMP_FILE = '%splain' % REMOTE_UNIT_TEST_FOLDER
    TMP_CONTENT = 'This is some text'
    TMP_FILE2 = '%splain2' % REMOTE_UNIT_TEST_FOLDER
    TMP_FOLDER =  '%stest_folder/' % REMOTE_UNIT_TEST_FOLDER 
    TMP_FOLDER2 =  '%stest_folder2/' % REMOTE_UNIT_TEST_FOLDER 

    client = StorageBackEnd(load_config()['DROPBOX_TOKEN'])

    client.get_user_account()
    # Create
    if sys.version_info[0] > 2:
        # Encoding for Python3
        TMP_CONTENT = str.encode(TMP_CONTENT)
    client.files_upload(TMP_CONTENT, TMP_FILE)
    print("File upload %s" % green("OK"))

    # Check existance file
    remote = client.file_type(TMP_FILE)
    assert remote['status'] == 'online', "Status not online on file_type"
    assert remote['content'] == 'file' , "Dropbox file creation failed"
    print("File existance %s" % green("OK"))

    # Check content
    remote = client.file_download(TMP_FILE)
    assert remote['status'] == 'online', "Status not online on file_download"
    if sys.version_info[0] > 2:
        # Encoding for Python3
        remote_content = str.encode(remote_content)
    assert TMP_CONTENT == remote['content'], \
        "Retrieval of remote content failed"
    print("Content check %s" % green("OK"))

    # List folders does not die
    remote = client.list_folders(REMOTE_UNIT_TEST_FOLDER[:-1])
    assert remote['status'] == 'online', "Status not online on list_folders"
    print("Listing files %s" % green("OK"))

    # Move
    client.files_copy(TMP_FILE, TMP_FILE2)
    client.files_delete(TMP_FILE)
    # Check non existance file
    remote = client.file_type(TMP_FILE)
    assert remote['status'] == 'online' and remote['content'] is None, \
        "File removal failed"
    print("Move files %s" % green("OK"))

    # Make folder
    client.make_directory(TMP_FOLDER[:-1])
    remote = client.file_type(TMP_FOLDER[:-1])
    assert remote['status'] == 'online' and remote['content'] == 'dir', \
        "Folder creation failed"
    print("Make folder %s" % green("OK"))

    # Move folder
    client.files_copy(TMP_FOLDER[:-1], TMP_FOLDER2[:-1])
    remote = client.file_type(TMP_FOLDER2[:-1])
    assert remote['status'] == 'online' and remote['content'] == 'dir', \
        "Folder creation failed"
    client.files_delete(TMP_FOLDER[:-1])
    remote = client.file_type(TMP_FOLDER[:-1])
    assert remote['status'] == 'online' and remote['content'] is None, \
        "Folder removal failed"
    print("Move folder %s" % green("OK"))

    # Clean-up
    client.files_delete(REMOTE_UNIT_TEST_FOLDER[:-1])
    remote = client.file_type(REMOTE_UNIT_TEST_FOLDER[:-1])
    assert remote['status'] == 'online' and remote['content'] is None, \
        "Folder removal failed"

if __name__ == '__main__':

    try:
        start_environment(backend_name='dropbox')
        test_main()
        reset_environment(sucess=True)

    except Exception as exception:
        # Ensure we restore the original config
        reset_environment()
        # Reraise error
        if sys.version_info[0] > 2:
            raise exception.with_traceback(sys.exc_info()[2])
        else:
            t, v, tb = sys.exc_info()
            raise(t, v, tb)
