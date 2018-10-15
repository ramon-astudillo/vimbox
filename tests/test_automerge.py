import os
import copy
import sys
import shutil
import vimbox
from vimbox.__main__ import main
from vimbox.crypto import get_path_hash
from vimbox.local import (
    load_config,
    get_local_file,
    write_config,
    CONFIG_FILE,
)


# Name of the folder where we carry on the test
UNIT_TEST_FOLDER = '/14s52fr34G2R3tH42341/'


def read_file(file_path):
    with open(file_path) as fid:
        return fid.read()


FAKE_REMOTE_STORAGE = os.path.realpath(
    "/%s/../tests/.fake_remote/" % os.path.dirname(vimbox.__file__)
)


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


def test_main(config):

    # Get initial config, set backend to fake
    # FIXME: If this dies it will leave the backend set to fake
    config['backend_name'] = 'fake'

    TMP_FILE = '%splain' % UNIT_TEST_FOLDER
    TMP_CONTENT = 'This is some text'

    # AUTOMERGE: Append/Prepend
    TMP_FILE = '%soriginal' % UNIT_TEST_FOLDER
    main(['-f', TMP_FILE, TMP_CONTENT], config=config)
    # Simulate append remote edition
    written_content = read_remote_content(TMP_FILE)
    write_remote_content(TMP_FILE, TMP_CONTENT + "\nAppended line")
    # Edit should merge files
    from vimbox.remote.primitives import VimboxClient
    client = VimboxClient()
    client.edit(TMP_FILE, automerge={'append', 'prepend'}, diff_mode=True)
    # Simulate prepend remote edition
    written_content = read_remote_content(TMP_FILE)
    write_remote_content(TMP_FILE,  "Prepended line\n" + written_content)
    # Edit should merge files
    client.edit(TMP_FILE, automerge={'append', 'prepend'}, diff_mode=True)

    # AUTOMERGE: Insert
    # Simulate insert in remote edition
    written_sentences = read_remote_content(TMP_FILE).split('\n')
    written_sentences.insert(1, 'Inserted 1')
    written_sentences.insert(2, 'Inserted 2')
    written_sentences.insert(4, 'Inserted 3')
    write_remote_content(TMP_FILE,  "\n".join(written_sentences))
    # Edit should merge files
    client.edit(TMP_FILE, automerge=['insert'], diff_mode=True)

    # AUTOMERGE: Valid line modification
    written_sentences = read_remote_content(TMP_FILE).split('\n')
    written_sentences[3] = '<ignore_me> ' + written_sentences[3] + ' <me too>'
    write_remote_content(TMP_FILE,  "\n".join(written_sentences))
    # Edit should merge files
    client.edit(
        TMP_FILE,
        automerge={'ignore_edit': '^<ignore_me> | <me too>'},
        diff_mode=True
    )


def reset_environment(original_config=None):
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
    if original_config:
        print("Restored config before tests")
        write_config(CONFIG_FILE, original_config)
    else:
        return load_config()


if __name__ == '__main__':

    original_config = reset_environment()
    test_main(copy.deepcopy(original_config))
    reset_environment(original_config)
    exit(1)

    try:
        original_config = reset_environment()
        test_main(copy.deepcopy(original_config))
        reset_environment(original_config)

    except Exception as exception:
        # Ensure we restore the original config
        reset_environment(original_config)
        # Reraise error
        if sys.version_info[0] > 2:
            raise exception.with_traceback(sys.exc_info()[2])
        else:
            t, v, tb = sys.exc_info()
            raise(t, v, tb)
