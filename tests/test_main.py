import os
import copy
import sys
import shutil
import vimbox
from vimbox.__main__ import main
from vimbox.crypto import get_path_hash
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


FAKE_REMOTE_STORAGE = os.path.realpath(
    "/%s/../tests/.fake_remote/" % os.path.dirname(vimbox.__file__)
)


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
    config['backend_name'] = 'fake'

    TMP_FILE = '%splain' % UNIT_TEST_FOLDER
    TMP_CONTENT = 'This is some text'
    TMP_FILE2 = '%splain2' % UNIT_TEST_FOLDER

    # Files in this computer
    local_file = get_local_file(TMP_FILE, config=config)
    remote_file = get_remote_path(TMP_FILE)

    # NORMAL FILE
    read_config = load_config()
    # Creation
    main(['-f', TMP_FILE, TMP_CONTENT], config=config)
    # Check file and content are in the remote
    assert os.path.isfile(remote_file), "File creation failed"
    written_content = read_remote_content(TMP_FILE)
    assert TMP_CONTENT == written_content, "File content does not match"
    # Check a local copy was created (if intended)
    assert os.path.isfile(local_file), \
        "Creation of local file %s failed" % local_file
    # Check if the folder was added to the cache
    read_config = load_config()
    dirname = "%s/" % os.path.dirname(TMP_FILE)
    assert dirname in read_config['cache'], "Register in cache failed"

    # Remove non existing file should not die
    main(['rm', TMP_FILE + '_not_real'], config=config)

    # Non-empty folder removal should fail
    # NOTE: This protection is at VimboxClient level
    failed = False
    try:
        main(['rm', '-R', dirname], config=config)
    except OSError:
        failed = True
    assert failed, "Failed to raise exception on deleting non empty folder"

    # Move file

    # This tests both copy and remove
    main(['mv', TMP_FILE, TMP_FILE2], config=config)
    # Original file was removed
    # Check fake remote file was removed
    assert not os.path.isfile(remote_file), \
        "Removal of remote file %s failed" % remote_file
    # Check local file was removed
    assert not os.path.isfile(local_file), \
        "Removal of local file %s failed" % local_file
    # Check new file was created
    remote_file2 = get_remote_path(TMP_FILE2)
    assert os.path.isfile(remote_file2), "File creation failed"

    # Empty folder removal
    main(['rm', TMP_FILE2], config=config)
    main(['rm', '-R', dirname], config=config)
    # Check fake remote folder was removed
    remote_folder = get_remote_path(dirname)
    assert not os.path.isdir(remote_folder), "Removal of remote folder failed"
    # Check local file was removed
    local_folder = get_local_file(dirname, config=config)
    assert not os.path.isdir(local_folder), "Removal of local folder failed"
    # Check the file was removed from the cache
    read_config = load_config()
    assert dirname not in read_config['cache'], "Removal from cache failed"

    FAKE_FILE_ENCRYPTED = '/14s52fr34G2R3tH42341/encrypted'
    FAKE_SECRET_CONTENT = "This is some encrypted text"

    # TODO: Unregister folders when deleting last file

    # ENCRYPTED FILE CREATION
    PASSWORD = 'dummy'
    #
    main(
        ['-e', FAKE_FILE_ENCRYPTED, FAKE_SECRET_CONTENT],
        config=config,
        password=PASSWORD
    )
    # Check file and content are in the remote
    fake_file_encrypted_hash = get_path_hash(FAKE_FILE_ENCRYPTED)
    assert os.path.isfile(get_remote_path(fake_file_encrypted_hash)),\
        "File creation failed"
    written_content = read_remote_content(fake_file_encrypted_hash)
    assert FAKE_SECRET_CONTENT != written_content, \
        "File content is not enctypted!"
    # Check if the folder was added to the cache
    dirname = "%s/" % os.path.dirname(FAKE_FILE_ENCRYPTED)
    read_config = load_config()
    assert dirname in read_config['cache'], "Register in cache failed"
    # Check if path hash was added to the list
    hash_entry = (fake_file_encrypted_hash, FAKE_FILE_ENCRYPTED)
    assert hash_entry in read_config['path_hashes'].items(), \
        "Register of path hash failed"

    # Encrypted file removal
    main(['rm', FAKE_FILE_ENCRYPTED], config=config)
    # Check if path hash was removed from the list
    hash_entry = (fake_file_encrypted_hash, FAKE_FILE_ENCRYPTED)
    read_config = load_config()
    assert hash_entry not in read_config['path_hashes'].items(), \
        "Removal of path hash failed"

    # TODO: Move encrypted files.


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
        t, v, tb = sys.exc_info()
        raise t, v, tb
