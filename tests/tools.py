import os
import sys
import shutil
import vimbox
from vimbox.diogenes import style
from vimbox import local


green = style(font_color='light green')

# Name of the folder where we carry on the test
if hasattr(sys, 'real_prefix'):
    ROOT_FOLDER = "%s/.vimbox/" % sys.prefix
else:
    ROOT_FOLDER = "%s/.vimbox/" % os.environ['HOME']
# DATA storage for unit test
REMOTE_UNIT_TEST_FOLDER = '/.vimbox_unit_test/'


def read_file(file_path):
    with open(file_path) as fid:
        return fid.read()


def read_remote_content(remote_file):
    true_path = local.get_remote_path(remote_file)
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


def reset_folder(folder_path, delete=False, backend_name=None):

    if backend_name is None:

        # Fake backend
        if os.path.isdir(folder_path):
            shutil.rmtree(folder_path)
            print("Reset %s" % folder_path)
        if delete:
            os.mkdirs(folder_path)

    elif backend_name == 'dropbox':

        # Dropbox
        from vimbox.remote.primitives import VimboxClient
        from vimbox.local import load_config
        # Extra sanity check
        client = StorageBackEnd(load_config()['DROPBOX_TOKEN'])
        import ipdb;ipdb.set_trace(context=30)
        if client.file_type(REMOTE_UNIT_TEST_FOLDER[:-1])['content']:
            client.files_delete(REMOTE_UNIT_TEST_FOLDER[:-1])
        if delete:
            client.make_directory(REMOTE_UNIT_TEST_FOLDER[:-1])

    else:
        raise Exception("%s backend not supported in tests" % backend_name)


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


def start_environment(**config_delta):
    """
    Create a folder for tests, store a copy of the config
    """

    # Fake remote storage
    backend_name = config_delta.get('backend_name', None)
    assert REMOTE_UNIT_TEST_FOLDER[:-1] == '/.vimbox_unit_test', \
        "CHANGING UNIT TEST FOLDER CAN LEAD TO DATA LOSS"
    reset_folder(REMOTE_UNIT_TEST_FOLDER, backend_name=backend_name)

    # Overload some config fields if solicited
    original_config = local.load_config()
    test_config = {
        'DROPBOX_TOKEN': original_config['DROPBOX_TOKEN'],
        'backend_name': original_config['backend_name'],
        'cache': {},
        'path_hashes': {},
        'remote_root': None,
        'remove_local': False
    }
    if config_delta:
        for key, value in config_delta.items():
            test_config[key] = value
    # Save new config
    unit_test_config = "%s/unit_test_%s" % (
        os.path.dirname(local.CONFIG_FILE),
        os.path.basename(local.CONFIG_FILE)
    )
    local.write_config(unit_test_config, test_config)
    local.CONFIG_FILE = unit_test_config
    print("Using config %s" % unit_test_config)

    return unit_test_config


def reset_environment(sucess=False):
    """
    - Remove folder simulating storage in remote
    - Remove folder in the local vimbox cache (THIS IS THE ACTUAL CACHE)
    - keep original config to restore it later
    """
    # Local storage
    reset_folder(UNIT_TEST_FOLDER, delete=True)

    # Remove overloaded config
    unit_test_config = "%s/unit_test_%s" % (
        os.path.dirname(local.CONFIG_FILE),
        os.path.basename(local.CONFIG_FILE)
    )
    os.remove(unit_test_config)

    # Inform user
    if sucess:
        print("Test was %s" % green("OK"))


def run_in_environment(test_function, debug=False):

    if debug:
        start_environment(backend_name='dropbox')
        test_function()
        reset_environment(sucess=True)

    else:
        try:
            start_environment(backend_name='dropbox')
            test_function()
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
