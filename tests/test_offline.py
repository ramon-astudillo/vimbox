import os
import copy
import sys
from vimbox.__main__ import main
from vimbox.local import load_config, get_local_file
from tools import run_in_environment, REMOTE_UNIT_TEST_FOLDER


def test_main():

    # Creation
    tmp_file = '%s/folder1/plain' % REMOTE_UNIT_TEST_FOLDER
    main(['-f', tmp_file, 'This is some text'])
    # Check a local copy was created (if intended)
    assert os.path.isfile(get_local_file(tmp_file)), \
        "Creation of local file %s failed" % tmp_file

    tmp_file = '%s/folder1/encrypted' % REMOTE_UNIT_TEST_FOLDER
    worked = main(
        ['-e', tmp_file, 'This is some encrypted text'], password='dummy'
    )
    assert not worked, "Should not be able to create encrypted file offline"
    assert not main(['rm', tmp_file]), \
        "Should not be able to remove files offline"
    assert not main(['cp', tmp_file, tmp_file + '2']), \
        "Should not be able to copy files offline"
    tmp_folder = '%s/folder1/folder2/' % REMOTE_UNIT_TEST_FOLDER
    assert not main(['mkdir', tmp_folder]), \
        "Should not be able to make folder offline"


if __name__ == '__main__':
    run_in_environment(test_main, debug=True, backend_name='fake-offline')
