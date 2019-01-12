import os
import copy
import sys
from vimbox.__main__ import main
from vimbox.crypto import get_path_hash
from vimbox.local import load_config, get_local_file
from tools import run_in_environment, green, REMOTE_UNIT_TEST_FOLDER


def hash_is_registered(encrypted_file):
    key = (get_path_hash(encrypted_file), encrypted_file)
    return key in load_config()['path_hashes'].items()


def test_main(backend_name):

    # SIMPLE COLLISIONS

    # Collision create plain, create encrypted
    plain_file = '%sfolder1/plain' % REMOTE_UNIT_TEST_FOLDER
    assert main(['-f', plain_file, 'Cosa mariposa'])
    assert main(['ls', plain_file], verbose=0), "Creating file failed"
    # Try to overwrite it with an encrypted one of same name
    assert not main(['-e', plain_file, 'Otra cosa mariposa'],
                    password='dummy'), "Collision with plain file"
    print("Collision create plain, create encrypted %s" % green("OK"))

    # Collision create encrypted, create plain
    encrypted_file = '%sfolder1/folder2/encrypted' % REMOTE_UNIT_TEST_FOLDER
    assert main(['-e', encrypted_file, 'This is secret'], password='dummy')
    assert main(['ls', encrypted_file], verbose=0), \
        "Creating encrypted file failed"
    # Try to overwrite it with an encrypted one of same name
    assert not main(['-f', encrypted_file, 'Other secret']), \
        "Collision with encrypted filefile"
    print("Collision create encrypted, create plain %s" % green("OK"))

    # Collision create plain, create folder
    failed = False
    try:
        main(['mkdir', plain_file + '/']), "mkdir collision"
    except AssertionError:
        failed = True
    assert failed, "Collision create plain, create folder did not happen"
    print("Collision create plain, create folder %s" % green("OK"))

    # Collision create encrypted, create folder
    failed = False
    try:
        main(['mkdir', encrypted_file + '/']), "mkdir collision"
    except AssertionError:
        failed = True
    assert failed, "Collision create encrypted, create folder"
    print("Collision create encrypted, create folder %s" % green("OK"))

    # MOVES

    # Move folder with encrypted file
    source_folder = '%sfolder1/folder2/' % REMOTE_UNIT_TEST_FOLDER
    target_folder = '%sfolder3/' % REMOTE_UNIT_TEST_FOLDER
    moved_encrypted_file = \
        '%sfolder3/folder2/encrypted' % REMOTE_UNIT_TEST_FOLDER
    assert main(['mkdir', target_folder])
    assert main(['mv', source_folder, target_folder])
    assert main(['ls', moved_encrypted_file], verbose=0), \
        "Moving folder with encrypted file failed"
    assert not hash_is_registered(source_folder), \
        "Unregister file hash when removing folder failed"
    assert hash_is_registered(moved_encrypted_file), \
        "Register file hash when removing folder failed"
    assert target_folder in load_config()['cache'], \
        "Adding to cache failed"
    print("Move encrypted %s" % green("OK"))

    # Create an encrypted file and root and try to overwrite it as plain
    encrypted_file2 = '%sencrypted2' % REMOTE_UNIT_TEST_FOLDER
    assert main(
        ['-e', encrypted_file2, 'Some encrypted data'],
        password='pass'
    )
    assert main(['ls', encrypted_file2], verbose=0)
    assert not main(['-f', encrypted_file2, 'Here is some more content'])
    print("encrypted file plain text collision %s" % green("OK"))

    # Fail at moving a file overwriting an encrypted file
    assert not main(['mv', encrypted_file2, moved_encrypted_file]), \
        "move collision"
    print("Encrypted file moved file collision %s" % green("OK"))


if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] in ['fake', 'dropbox']:
        backend_name = sys.argv[1]
    else:
        raise ValueError("Expected backend_name (fake, dropbox)")
    run_in_environment(test_main, debug=True, backend_name=backend_name)
