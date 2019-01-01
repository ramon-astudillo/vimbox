"""
- client side stuff regarding encryption
"""
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
    read_remote_content,
    is_local_file,
    is_local_dir,
    is_fake_remote_file,
    is_fake_remote_dir
)


def hash_is_registered(encrypted_file):
    key = (get_path_hash(encrypted_file), encrypted_file)
    return key in load_config()['path_hashes'].items()


def test_main():

    # NOTE: start_environment() has overloaded local.CONFIG_FILE

    encrypted_file = '%sencrypted' % REMOTE_UNIT_TEST_FOLDER
    encrypted_content = 'This is some text'

    # EDIT
    # Basic file creation local, cache, remote and has list
    assert main(['-e', encrypted_file, encrypted_content], password='dummy')
    assert is_local_file(encrypted_file), "Local file not created"
    assert encrypted_content == \
        read_remote_content(encrypted_file, password='dummy'), \
        "Local and remote content do not match"
    assert is_fake_remote_file(encrypted_file, password='dummy'), \
        "Remote file not created"
    assert "%s/" % os.path.dirname(encrypted_file) in load_config()['cache'], \
        "Register in cache failed"
    print("Basic file creation local, cache and remote %s" % green("OK"))
    assert hash_is_registered(encrypted_file), "Register in hash list failed"

    # MOVE
    # Move files
    folder_at_root = '%sfolder1/' % REMOTE_UNIT_TEST_FOLDER
    encrypted_file2 = '%sencrypted2' % folder_at_root
    assert main(['mkdir', folder_at_root]), "Could not create folder"
    assert main(['mv', encrypted_file, encrypted_file2])
    assert not is_fake_remote_file(encrypted_file, password='dummy'), \
        "Removal of encrypted file in remote failed"
    assert not is_local_file(encrypted_file), "Removal of local file failed"
    assert is_fake_remote_file(encrypted_file2, password='dummy'), \
        "creation of encrypted file in remote failed"
    assert is_local_file(encrypted_file2), "creation of local file failed"
    assert hash_is_registered(encrypted_file2), \
        "Register moved target file in hash list failed"
    print("Move file %s" % green("OK"))

    # Rename folder
    folder2 = '%sfolder2/' % REMOTE_UNIT_TEST_FOLDER
    moved_encrypted_file2 = "%s%s" % \
        (folder2, os.path.basename(encrypted_file2))
    assert main(['mv', folder_at_root, folder2])
    assert is_local_file(moved_encrypted_file2), \
        "File inside folder was not moved in local"
    assert is_fake_remote_file(moved_encrypted_file2, password='dummy'), \
        "File inside folder was not moved in remote"
    assert not is_local_file(encrypted_file2), \
        "File inside folder was not removed in local"
    assert not is_fake_remote_file(encrypted_file2, password='dummy'), \
        "File inside folder was not removed in remote"
    assert hash_is_registered(moved_encrypted_file2), \
        "Register moved target file in hash list failed"

    # REMOVE
    # remove folder (cache, local, remote)
    assert main(['rm', '-R', folder2])
    assert not is_fake_remote_dir(folder2), \
        "Removal of remote folder failed"
    assert not is_local_dir(folder2), "Removal of local folder failed"
    assert folder2 not in load_config()['cache'], \
        "Removal from cache failed"
    assert not hash_is_registered(moved_encrypted_file2), \
        "Unregister file when removing folder failed"
    print("Remove folder %s" % green("OK"))


if __name__ == '__main__':
    run_in_environment(test_main, backend_name='fake', debug=True)
