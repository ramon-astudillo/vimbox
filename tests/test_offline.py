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

    # NORMAL FILE
    read_config = load_config()

    # HERE: Check solving offline by rising up connection error up to __main__
    # and fixing it there

    # Creation
    main(['-f', '/folder1/plain', 'This is some text'])
    # Check a local copy was created (if intended)
    assert os.path.isfile(get_local_file('/folder1/plain')), \
        "Creation of local file %s failed" % '/folder1/plain'

    # All other attempts should give primitives.VimboxOfflineError


if __name__ == '__main__':

    try:
        start_environment(backend_name='fake-offline')
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
