import os
import copy
import sys
from vimbox.__main__ import main
from vimbox.crypto import get_path_hash
from vimbox.local import load_config, get_local_file
from tools import run_in_environment, green, REMOTE_UNIT_TEST_FOLDER


def test_main():

    main(['-f', '%s/folder1/plain' % REMOTE_UNIT_TEST_FOLDER, 'Cosa mariposa'])
    assert main(
        ['ls', '%s/folder1/plain' % REMOTE_UNIT_TEST_FOLDER], verbose=0
    )

    main(['-e', '%s/folder1/folder2/encrypted' % REMOTE_UNIT_TEST_FOLDER,
          'This is secret'], password='dummy')
    assert main([
        'ls',
        '%s/folder1/folder2/encrypted' % REMOTE_UNIT_TEST_FOLDER],
        verbose=0
    )

    main(['mkdir', '%s/folder3/' % REMOTE_UNIT_TEST_FOLDER])
    main(['mv', '%s/folder1/folder2/' % REMOTE_UNIT_TEST_FOLDER,
          '%s/folder3/' % REMOTE_UNIT_TEST_FOLDER])
    assert main([
        'ls',
        '%s/folder3/folder2/encrypted' % REMOTE_UNIT_TEST_FOLDER
    ], verbose=0)
    print("Move encrypted %s" % green("OK"))

    # Create an encrypted file and root and try to overwrite it
    main(['-e', '%s/secret_file' % REMOTE_UNIT_TEST_FOLDER,
          'Some encrypted data'],
         password='pass')
    assert main(['ls', '%s/secret_file' % REMOTE_UNIT_TEST_FOLDER], verbose=0)
    assert not main(['-f', '%s/secret_file' % REMOTE_UNIT_TEST_FOLDER,
                     'Here is some more content'])
    print("Create encrypted in root %s" % green("OK"))

    # Fail at creating folder with same name
    assert not main(['mkdir', '%s/secret_file/' % REMOTE_UNIT_TEST_FOLDER])
    print("Encrypted file folder collision %s" % green("OK"))

    # Fail at moving a file overwriting another file
    main(['mv', '%s/secret_file' % REMOTE_UNIT_TEST_FOLDER,
          '%s/folder3/folder2/encrypted' % REMOTE_UNIT_TEST_FOLDER])
    print("Encrypted file moved file collision %s" % green("OK"))

    # Cleanup
    if main(['ls', '%s/' % REMOTE_UNIT_TEST_FOLDER], verbose=0):
        main(['rm', '-R', '%s/' % REMOTE_UNIT_TEST_FOLDER])


if __name__ == '__main__':
    run_in_environment(test_main, debug=True)
