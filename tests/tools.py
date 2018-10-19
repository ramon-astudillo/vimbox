import os
import sys
import shutil
import vimbox
from vimbox.diogenes import style
from vimbox.local import (
    load_config,
    get_local_file,
    write_config,
    CONFIG_FILE,
)
green = style(font_color='light green')

# Name of the folder where we carry on the test
UNIT_TEST_FOLDER = '/14s52fr34G2R3tH42341/'
FAKE_REMOTE_STORAGE = os.path.realpath(
    "/%s/../tests/.fake_remote/" % os.path.dirname(vimbox.__file__)
)


def read_file(file_path):
    with open(file_path) as fid:
        return fid.read()


def get_remote_path(remote_file):
    return "%s/%s" % (FAKE_REMOTE_STORAGE, remote_file)


def read_remote_content(remote_file):
    true_path = get_remote_path(remote_file)
    with open(true_path, 'rb') as fid:
        text = fid.read()

    # Python3
    if text and sys.version_info[0] > 2:
        try:
            text = text.decode("utf-8")
        except UnicodeDecodeError:
            # Encrypted content
            pass

    return text


def write_remote_content(remote_file, remote_content):
    true_path = get_remote_path(remote_file)

    # Python3
    if sys.version_info[0] > 2:
        try:
            remote_content = remote_content.encode("utf-8")
        except UnicodeDecodeError:
            # Encrypted content
            pass

    with open(true_path, 'wb') as fid:
        fid.write(remote_content)


def reset_environment(original_config=None, sucess=False):
    """
    - Remove folder simulating storage in remote
    - Remove folder in the local vimbox cache (THIS IS THE ACTUAL CACHE)
    - keep original config to restore it later
    """
    fake_remote_storage = get_remote_path(UNIT_TEST_FOLDER)
    local_storage = get_local_file(UNIT_TEST_FOLDER)
    if os.path.isdir(fake_remote_storage):
        shutil.rmtree(fake_remote_storage)
    if os.path.isdir(local_storage):
        shutil.rmtree(local_storage)
    if sucess:
        print("Test was %s" % green("OK"))
    if original_config:
        print("Restored config before tests")
        write_config(CONFIG_FILE, original_config)
    else:
        return load_config()
