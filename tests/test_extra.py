import os
import copy
import sys
from vimbox.__main__ import main
from vimbox.crypto import get_path_hash
from vimbox.local import load_config, get_local_file
from tools import run_in_environment, green, REMOTE_UNIT_TEST_FOLDER


def test_main():

    # Create plain file
    plain_file = '%sfolder1/plain' % REMOTE_UNIT_TEST_FOLDER
    assert main(['-f', plain_file, 'Cosa mariposa'])
    assert main(['ls', plain_file], verbose=0), "Creating file failed"

    # Create encrypted file
    encrypted_file = '%sfolder1/folder2/encrypted' % REMOTE_UNIT_TEST_FOLDER
    assert main(['-e', encrypted_file, 'This is secret'], password='dummy')
    assert main(['ls', encrypted_file], verbose=0), \
        "Creating encrypted file failed"

    # Move folder with encrypted file
    source_folder = '%sfolder1/folder2/' % REMOTE_UNIT_TEST_FOLDER
    target_folder = '%sfolder3/' % REMOTE_UNIT_TEST_FOLDER
    moved_encrypted_file = \
        '%sfolder3/folder2/encrypted' % REMOTE_UNIT_TEST_FOLDER
    assert main(['mkdir', target_folder])
    assert main(['mv', source_folder, target_folder])
    assert main(['ls', moved_encrypted_file], verbose=0), \
        "Moving folder with encrypted file failed"
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

    # Fail at creating folder with same name
    assert not main(['mkdir', encrypted_file2 + '/']), "mkdir collision"
    print("Encrypted file folder collision %s" % green("OK"))

    # Fail at moving a file overwriting an encrypted file
    assert not main(['mv', encrypted_file2, moved_encrypted_file]), \
        "move collision"
    print("Encrypted file moved file collision %s" % green("OK"))


if __name__ == '__main__':
    run_in_environment(test_main, debug=True)
