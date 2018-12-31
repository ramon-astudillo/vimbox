import os
import copy
import sys
from vimbox.__main__ import main
from vimbox.crypto import get_path_hash
from vimbox.local import load_config, get_local_file
from vimbox.remote.fake_backend import get_fake_remote_local_path
from tools import (
    green,
    run_in_environment,
    REMOTE_UNIT_TEST_FOLDER,
    read_remote_content
)


def test_main():

    # NOTE: start_environment() has overloaded local.CONFIG_FILE

    TMP_FILE = '%splain' % REMOTE_UNIT_TEST_FOLDER
    TMP_CONTENT = 'This is some text'
    TMP_FILE2 = '%splain2' % REMOTE_UNIT_TEST_FOLDER
    TMP_FOLDER = '%stest_folder/' % REMOTE_UNIT_TEST_FOLDER
    TMP_FOLDER2 = '%stest_folder2/' % REMOTE_UNIT_TEST_FOLDER

    # Files in this computer
    local_file = get_local_file(TMP_FILE)
    remote_file = get_fake_remote_local_path(TMP_FILE)

    # FILE CREATION
    # Creation
    main(['-f', TMP_FILE, TMP_CONTENT])
    # Check file and content are in the remote
    assert os.path.isfile(remote_file), "File creation failed"
    written_content = read_remote_content(TMP_FILE)
    assert TMP_CONTENT == written_content, "File content does not match"
    # Check a local copy was created (if intended)
    assert os.path.isfile(local_file), \
        "Creation of local file %s failed" % local_file
    # Check if the folder was added to the cache
    dirname = "%s/" % os.path.dirname(TMP_FILE)
    assert dirname in load_config()['cache'], "Register in cache failed"
    print("File creation %s" % green("OK"))

    # REMOVE NON EXISTING FILE
    main(['rm', TMP_FILE + '_not_real'])
    print("Remove non-existing %s" % green("OK"))

    # MOVE FILE
    # This tests both copy and remove
    main(['mv', TMP_FILE, TMP_FILE2])
    # Original file was removed
    # Check fake remote file was removed
    assert not os.path.isfile(remote_file), \
        "Removal of remote file %s failed" % remote_file
    # Check local file was removed
    assert not os.path.isfile(local_file), \
        "Removal of local file %s failed" % local_file
    # Check new file was created
    remote_file2 = get_fake_remote_local_path(TMP_FILE2)
    assert os.path.isfile(remote_file2), "File creation failed"
    print("Move file %s" % green("OK"))

    TMP_FOLDER = '%stest_folder/' % REMOTE_UNIT_TEST_FOLDER
    TMP_FOLDER2 = '%stest_folder2/' % REMOTE_UNIT_TEST_FOLDER

    # MOVE FOLDER
    main(['mkdir', TMP_FOLDER])
    main(['mv', TMP_FOLDER, TMP_FOLDER2])
    # Original file was removed
    # Check fake remote file was removed
    assert not os.path.isdir(get_fake_remote_local_path(TMP_FOLDER)), \
        "Removal of remote file %s failed" % remote_file
    # Check local file was removed
    assert not os.path.isdir(get_local_file(TMP_FOLDER)), \
        "Removal of local file %s failed" % local_file
    # Check new file was created
    assert os.path.isdir(get_fake_remote_local_path(TMP_FOLDER2)), \
        "File creation failed"
    print("Move folder %s" % green("OK"))

    # REMOVE FOLDER
    main(['rm', '-R', TMP_FOLDER2])
    # Check fake remote folder was removed
    remote_folder = get_fake_remote_local_path(TMP_FOLDER2)
    assert not os.path.isdir(remote_folder), "Removal of remote folder failed"
    # Check local file was removed
    local_folder = get_local_file(TMP_FOLDER2)
    assert not os.path.isdir(local_folder), "Removal of local folder failed"
    # Check the file was removed from the cache
    read_config = load_config()
    assert TMP_FOLDER2 not in read_config['cache'], "Removal from cache failed"
    print("Remove folder %s" % green("OK"))

    FAKE_FILE_ENCRYPTED = '%sencrypted' % TMP_FOLDER2
    FAKE_SECRET_CONTENT = "This is some encrypted text"

    # ENCRYPTED FILE CREATION
    main(['-e', FAKE_FILE_ENCRYPTED, FAKE_SECRET_CONTENT], password='dummy')
    # Check file and content are in the remote
    fake_file_encrypted_hash = get_path_hash(FAKE_FILE_ENCRYPTED)
    assert \
        os.path.isfile(get_fake_remote_local_path(fake_file_encrypted_hash)),\
        "File creation failed"
    written_content = read_remote_content(fake_file_encrypted_hash)
    assert FAKE_SECRET_CONTENT != written_content, \
        "File content is not enctypted!"
    # Check if the folder was added to the cache
    dirname = "%s/" % os.path.dirname(FAKE_FILE_ENCRYPTED)
    assert dirname in load_config()['cache'], "Register in cache failed"
    # Check if path hash was added to the list
    hash_entry = (fake_file_encrypted_hash, FAKE_FILE_ENCRYPTED)
    assert hash_entry in load_config()['path_hashes'].items(), \
        "Register of path hash failed"
    print("Encrypted file creation %s" % green("OK"))

    # MOVE FOLDER WITH ENCRYPTED FILES
    # This tests both copy and remove
    # FIXME: HARDEN copy
    main(['mv', TMP_FOLDER2, TMP_FOLDER])
    # Original file was removed
    # Check fake remote file was removed
    assert not os.path.isdir(get_fake_remote_local_path(TMP_FOLDER2)), \
        "Removal of remote dir %s failed" % \
        get_fake_remote_local_path(TMP_FOLDER2)
    # Check new dir was created
    assert os.path.isdir(get_fake_remote_local_path(TMP_FOLDER)), \
        "Dir creation failed"
    print("Move folder with encrypted files  %s" % green("OK"))
    # Check has was updated

    # ENCRYPTED FILE REMOVAL
    FAKE_FILE_ENCRYPTED = '%sencrypted' % TMP_FOLDER
    main(['rm', FAKE_FILE_ENCRYPTED])
    # Check if path hash was removed from the list
    hash_entry = (fake_file_encrypted_hash, FAKE_FILE_ENCRYPTED)
    assert hash_entry not in load_config()['path_hashes'].items(), \
        "Removal of path hash failed"
    print("Encrypted file removal %s" % green("OK"))


if __name__ == '__main__':
    run_in_environment(test_main, backend_name='fake', debug=True)
