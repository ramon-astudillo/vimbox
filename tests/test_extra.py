import os
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


def test_main():

    main(['-f', '/.unit_test/folder1/plain', 'Cosa mariposa'])
    assert main(['ls', '/.unit_test/folder1/plain'], verbose=0)

    main(['-e', '/.unit_test/folder1/folder2/encrypted', 'This is secret'], 
         password='dummy')
    assert main(['ls', '/.unit_test/folder1/folder2/encrypted'], verbose=0)

    main(['mkdir', '/.unit_test/folder3/'])
    main(['mv', '/.unit_test/folder1/folder2/', '/.unit_test/folder3/'])
    assert main(['ls', '/.unit_test/folder3/folder2/encrypted'], verbose=0)
    print("Move encrypted %s" % green("OK"))

    # Create an encrypted file and root and try to overwrite it
    main(['-e', '/.unit_test/secret_file', 'Some encrypted data'], password='pass')
    assert main(['ls', '/.unit_test/secret_file'], verbose=0)
    assert not main(['-f', '/.unit_test/secret_file', 'Here is some more content'])
    print("Create encrypted in root %s" % green("OK"))

    # Fail at creating folder with same name
    assert not main(['mkdir', '/.unit_test/secret_file/'])
    print("Encrypted file folder collision %s" % green("OK"))

    # Fail at moving a file overwriting another file
    main(['mv', '/.unit_test/secret_file', '/.unit_test/folder3/folder2/encrypted'])
    print("Encrypted file moved file collision %s" % green("OK"))

    # Cleanup
    if main(['ls', '/.unit_test/'], verbose=0):
        main(['rm', '-R', '/.unit_test/'])

if __name__ == '__main__':

    try:
        start_environment(backend_name='fake')
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
