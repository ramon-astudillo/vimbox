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

    # Encrypted files created but not in hash list will not be seen when
    # creating a new file
    if main(['ls', '/folder1/']):
        main(['rm', '-R', '/folder1/'])
    if main(['ls', '/folder3/']):
        main(['rm', '-R', '/folder3/'])

    main(['-f', '/logs/temp/plain', 'Cosa mariposa'])
    assert main(['ls', '/logs/temp/plain'])

    main(['-e', '/folder1/folder2/encrypted', 'Cosa mariposa'], password='dummy')
    assert main(['ls', '/folder1/folder2/encrypted'])

    main(['mkdir', '/folder3/'])
    main(['mv', '/folder1/folder2/', '/folder3/'])
    main(['ls', '/folder3/folder2/'])
    assert main(['ls', '/folder3/folder2/encrypted'])

    # Create an encrypted file and root and try to overwrite it
    main(['-e', '/secret_file', 'Some encrypted data'], password='pass')
    assert main(['ls', '/secret_file'])
    assert not main(['-f', '/secret_file', 'Here is some more content'])

    # Fail at creating folder with same name
    assert not main(['mkdir', '/secret_file/'])

    # Cleanup
    if main(['ls', '/secret_file']):
        main(['rm', '/secret_file'])
    if main(['ls', '/folder1/']):
        main(['rm', '-R', '/folder1/'])
    if main(['ls', '/folder3/']):
        main(['rm', '-R', '/folder3/'])

if __name__ == '__main__':

    #start_environment(backend_name='fake')
    start_environment()
    test_main()
    reset_environment(sucess=True)
    exit()

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
