import os
import copy
import sys
from vimbox.__main__ import main
from vimbox.local import load_config, get_local_file
from tools import run_in_environment


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

    # TODO: All other attempts should give primitives.VimboxOfflineError


if __name__ == '__main__':
    run_in_environment(test_main, debug=True)
