"""
- client side stuff
- local file operations
- cache
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


def test_main(backend_name):

    # NOTE: start_environment() has overloaded local.CONFIG_FILE

    plain_file = '%splain' % REMOTE_UNIT_TEST_FOLDER
    plain_content = 'This is some text'

    # EDIT
    # Basic file creation local, cache and remote
    assert main(['-f', plain_file, plain_content])
    assert is_local_file(plain_file), "Local file not created"
    assert plain_content == read_remote_content(plain_file), \
        "Local and remote content do not match"
    assert is_local_file(plain_file), "Remote file not created"
    assert "%s/" % os.path.dirname(plain_file) in load_config()['cache'], \
        "Register in cache failed"
    print("Basic file creation local, cache and remote %s" % green("OK"))

    # MKDIR
    folder_at_root = '%sfolder1/' % REMOTE_UNIT_TEST_FOLDER
    assert main(['mkdir', folder_at_root]), "Could not create folder"
    assert is_local_dir(folder_at_root), "Local folder not created"
    assert is_fake_remote_dir(folder_at_root), "Remote folder not created"
    print("Folder creation %s" % green("OK"))

    # MOVE
    # Move files
    plain_file2 = '%splain2' % folder_at_root
    assert main(['mv', plain_file, plain_file2])
    assert not is_fake_remote_file(plain_file), "Removal of remote dir failed"
    assert not is_local_file(plain_file), "Removal of local file failed"
    assert is_fake_remote_file(plain_file2), "Creation of remote dir failed"
    assert is_local_file(plain_file2), "Creation of local file failed"
    print("Move file %s" % green("OK"))
    # Rename folder
    folder2 = '%sfolder2/' % REMOTE_UNIT_TEST_FOLDER
    moved_plain_file2 = "%s%s" % (folder2, os.path.basename(plain_file2))
    assert main(['mv', folder_at_root, folder2])
    assert is_local_file(moved_plain_file2), \
        "File inside folder was not moved in local"
    assert is_fake_remote_file(moved_plain_file2), \
        "File inside folder was not moved in remote"

    # REMOVE
    # Can not remove non existing file
    assert not main(['rm', plain_file + '_not_real']), \
        "Removing non-existing file should fail"
    print("Can not remove non existing file %s" % green("OK"))
    # remove folder (cache, local, remote)
    assert main(['rm', '-R', folder2])
    assert not is_fake_remote_dir(folder2), \
        "Removal of remote folder failed"
    assert not is_local_dir(folder2), "Removal of local folder failed"
    assert folder2 not in load_config()['cache'], \
        "Removal from cache failed"
    print("Remove folder %s" % green("OK"))


if __name__ == '__main__':
    run_in_environment(test_main, backend_name='fake', debug=True)
