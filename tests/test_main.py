import os
import sys
import codecs
import shutil
from vimbox.__main__ import main
from vimbox.local import (
    load_config,
    get_local_file,
    write_config,
    CONFIG_FILE,
    DEFAULT_CONFIG
)


def read_file(file_path):
    with open(file_path) as fid:
        return fid.read()

TEST_FOLDER = "%s/.fake_remote/" % os.path.realpath(os.path.dirname(__file__))


def get_remote_path(remote_file):
    return "%s/%s" % (TEST_FOLDER, remote_file)


def read_remote_content(remote_file):
    true_path = get_remote_path(remote_file)
    with codecs.open(true_path, 'r', 'utf-8') as fid:
        text = fid.read()
    return text


def test_main(config):

    TMP_FILE = '/14s52fr34G2R3tH42341/plain'
    TMP_CONTENT = "This is some text"
    TMP_FILE2 = '/14s52fr34G2R3tH42341/plain2'

    # Get initial config, set backend to fake
    # FIXME: If this dies it will leave the backend set to fake
    config['backend_name'] = 'fake'

    # Files in this computer
    local_file = get_local_file(TMP_FILE, config=config)
    remote_file = get_remote_path(TMP_FILE)

    # Remove temporal folder
    if os.path.isdir(TEST_FOLDER):
        shutil.rmtree(TEST_FOLDER)
        os.remove(local_file)

    # NORMAL FILE
    # Creation
    main(['-f', TMP_FILE, TMP_CONTENT], config=config)
    # Check file and content are in the remote
    assert os.path.isfile(remote_file), "File creation failed"
    written_content = read_remote_content(TMP_FILE)
    assert TMP_CONTENT == written_content, "File content does not match"
    # Check a local copy was created (if intended)
    assert os.path.isfile(local_file), \
        "Creation of local file %s failed" % local_file
    # Check if the folder was added to the cache
    dirname = "%s/" % os.path.dirname(TMP_FILE)
    assert dirname in config['cache'], "Register in cache failed"

    # Non-empty folder removal should fail
    failed = False
    try:
        main(['rm', '-R', dirname], config=config)
    except OSError as exception:
        failed = True
    assert failed, "Failed to raise exception on deleting non empty folder"

    # Move file

    # This tests both copy and remove
    main(['mv', TMP_FILE, TMP_FILE2], config=config)
    # Original file was removed
    # Check fake remote file was removed
    assert not os.path.isfile(remote_file), \
        "Removal of remote file %s failed" % remote_file
    # Check local file was removed
    assert not os.path.isfile(local_file), \
        "Removal of local file %s failed" % local_file
    # Check new file was created
    remote_file2 = get_remote_path(TMP_FILE2)
    assert os.path.isfile(remote_file2), "File creation failed"
    # Check local file was created
    local_file2 = get_local_file(TMP_FILE2, config=config)
    assert not os.path.isfile(get_local_file(local_file2)), \
        "Removal of local file %s failed" % local_file2

    # Empty folder removal
    main(['rm', TMP_FILE2], config=config)
    main(['rm', '-R', dirname], config=config)
    # Check fake remote folder was removed
    remote_folder = get_remote_path(dirname)
    assert not os.path.isdir(remote_folder), "Removal of remote folder failed"
    # Check local file was removed
    local_folder = get_local_file(dirname, config=config)
    assert not os.path.isdir(local_folder), "Removal of local folder failed"
    # Check the file was removed from the cache
    assert dirname not in config['cache'], "Removal from cache failed"

    TMP_FILE = '/14s52fr34G2R3tH42341/encrypted'
    TMP_CONTENT = "This is some encrypted text"

    # ENCRYPTED FILE CREATION
    main(['-e', TMP_FILE, TMP_CONTENT], config=config)
    # Check file and content are in the remote
    assert os.path.isfile(get_remote_path(TMP_FILE)), "File creation failed"
    written_content = read_remote_content(TMP_FILE)
    assert TMP_CONTENT != written_content, "File content is not enctypted!"
    # Check if the folder was added to the cache
    config = load_config()
    dirname = "%s/" % os.path.dirname(TMP_FILE)
    assert dirname in config['cache'], "Register in cache failed"

    # Disallow moving to other folder


if __name__ == '__main__':
    try:
        original_config = load_config()
        test_main(original_config)
    except Exception as exception:
        # Ensure we restore the original config
        t, v, tb = sys.exc_info()
        write_config(CONFIG_FILE, original_config)
        raise t, v, tb
