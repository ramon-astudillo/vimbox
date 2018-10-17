import os
import copy
import sys
import shutil
from vimbox.remote.primitives import auto_merge

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

    # AUTOMERGE: Append
    local_content = 'This is some text'
    remote_content = local_content + "\nAppended line"
    merged_content, merge_strategy = auto_merge(
        local_content,
        remote_content,
        {'append', 'prepend'}
    )
    assert merge_strategy == 'append', "Automerge appended line failed"
    assert merged_content == remote_content, "Automerge appended line failed"
    print("Automerge append OK")

    # AUTOMERGE: Append-line
    local_content = 'This is some text'
    remote_content = local_content + "Appended to line"
    merged_content, merge_strategy = auto_merge(
        local_content,
        remote_content,
        {'line-append'}
    )
    assert merge_strategy == 'line-append', "Automerge appended line failed"
    assert merged_content == remote_content, "Automerge appended line failed"
    print("Automerge line append OK")

    # AUTOMERGE: Prepend
    local_content = 'This is some text'
    remote_content = 'Prepended text\n' + local_content
    merged_content, merge_strategy = auto_merge(
        local_content,
        remote_content,
        {'append', 'prepend'}
    )
    assert merge_strategy == 'prepend', "Automerge prepended failed"
    assert merged_content == remote_content, "Automerge prepend failed"
    print("Automerge prepend OK")

    # AUTOMERGE: Prepend
    local_content = 'This is some text'
    remote_content = 'Prepended to line' + local_content
    merged_content, merge_strategy = auto_merge(
        local_content,
        remote_content,
        {'line-prepend'}
    )
    assert merge_strategy == 'line-prepend', "Automerge prepended line failed"
    assert merged_content == remote_content, "Automerge prepend line failed"
    print("Automerge line prepend OK")

    # AUTOMERGE: Insert
    local_lines = ['This is one sentence', 'This is another']
    remote_lines= list(local_lines)
    remote_lines.insert(1, 'Inserted 1')
    remote_lines.insert(2, 'Inserted 2')
    remote_lines.insert(4, 'Inserted 3')
    local_content = "\n".join(local_lines)
    remote_content = "\n".join(remote_lines)
    merged_content, merge_strategy = auto_merge(
        local_content,
        remote_content,
        {'insert'}
    )
    assert merge_strategy == 'insert', "Automerge prepended line failed"
    assert merged_content == remote_content, "Automerge insert line failed"
    print("Automerge insert OK")

    # AUTOMERGE: Valid line modification
    local_lines = ['this is one sentence', 'this is another']
    remote_lines= ['this is two sentences', 'this is another']
    local_content = "\n".join(local_lines)
    remote_content = "\n".join(remote_lines)
    merged_content, merge_strategy = auto_merge(
        local_content,
        remote_content,
        {'ignore-edit': '(.* is).*(sentence)s?'}
    )
    assert merge_strategy == 'ignore-edit', "Automerge ignore-edit failed"
    assert merged_content == remote_content, "Automerge ignore-edit failed"
    print("Automerge ignore-edit OK")

    # AUTOMERGE: Multiple cases
    local_lines = ['this is one sentence', 'this is another']
    remote_lines= [
        'this is two sentences',
        'I inserted something here',
        'prepended stuff this is another'
    ]
    local_content = "\n".join(local_lines)
    remote_content = "\n".join(remote_lines)
    merged_content, merge_strategy = auto_merge(
        local_content,
        remote_content,
        {
            'ignore-edit': '(.* is).*(sentence)s?',
            'insert' : True,
            'line-prepend': True
        }
    )
    assert merge_strategy == 'ignore-edit+insert+line-prepend', \
        "Automerge ignore-edit failed"
    assert merged_content == remote_content, "Automerge ignore-edit failed"
    print("Automerge ignore-edit OK")


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
