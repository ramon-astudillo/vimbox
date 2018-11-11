import os
import copy
import sys
from vimbox.__main__ import main
from vimbox.local import load_config, get_local_file
from tools import (
    start_environment,
    reset_environment,
    REMOTE_UNIT_TEST_FOLDER,
    green
)


def test_main():

    TMP_FILE = '%splain' % REMOTE_UNIT_TEST_FOLDER
    TMP_CONTENT = 'This is some text'
    TMP_FILE2 = '%splain2' % REMOTE_UNIT_TEST_FOLDER

    # Files in this computer
    local_file = get_local_file(TMP_FILE)

    # NORMAL FILE
    read_config = load_config()
    # Creation
    main(['-f', TMP_FILE, TMP_CONTENT])
    # Check a local copy was created (if intended)
    assert os.path.isfile(local_file), \
        "Creation of local file %s failed" % local_file
    # Check if the folder was added to the cache
    read_config = load_config()
    dirname = "%s/" % os.path.dirname(TMP_FILE)
    assert dirname in read_config['cache'], "Register in cache failed"
    print("Offline file creation %s" % green("OK"))

    # MOVE FILE
    # This tests both copy and remove
    main(['mv', TMP_FILE, TMP_FILE2])
    # Check local file was not removed
    assert os.path.isfile(local_file), \
        "local file %s can not be removed while offline" % local_file
    local_file2 = get_local_file(TMP_FILE2)
    assert not os.path.isfile(local_file2), \
        "local file %s can not be created by copy while offline" % local_file
    print("Offline move file%s" % green("OK"))

    # ENCRYPTED FILE CREATION
    # TODO: This returns with exit which will skip restablishing of config
#     FAKE_FILE_ENCRYPTED = '/14s52fr34G2R3tH42341/encrypted'
#     FAKE_SECRET_CONTENT = "This is some encrypted text"
#     PASSWORD = 'dummy'
#     #
#     # Creating ecrypted files while offline makes no sense
#     main(
#         ['-e', FAKE_FILE_ENCRYPTED, FAKE_SECRET_CONTENT],
#         config=config,
#         password=PASSWORD
#     )
#     local_encrypted = get_local_file(FAKE_FILE_ENCRYPTED)
#     assert not os.path.isfile(local_file2), \
#         "Should not create local file while offline if encrypted"


if __name__ == '__main__':

    try:
        start_environment(backend_name='fake-offline')
        test_main()
        reset_environment(sucess=True)

    except Exception as exception:
        # Ensure we restore the original config
        reset_environment(original_config)
        # Reraise error
        if sys.version_info[0] > 2:
            raise exception.with_traceback(sys.exc_info()[2])
        else:
            t, v, tb = sys.exc_info()
            raise(t, v, tb)
