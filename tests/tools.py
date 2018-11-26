import os
import sys
import shutil
import vimbox
from vimbox.diogenes import style
from vimbox import local


green = style(font_color='light green')

# Name of the folder where we carry on the test
REMOTE_UNIT_TEST_FOLDER = '/.unit_test/'
UNIT_TEST_FOLDER = os.path.realpath(
    "/%s/../tests/" % os.path.dirname(vimbox.__file__)
)
FAKE_REMOTE_STORAGE = os.path.realpath("%s/.fake_remote/" % UNIT_TEST_FOLDER)


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


def start_environment(**config_delta):
    """Create a folder for tests, store a copy of the config"""

    # Fake remote storage
    if config_delta.get('backend_name', None) == 'fake':
        if os.path.isdir(FAKE_REMOTE_STORAGE):
            shutil.rmtree(FAKE_REMOTE_STORAGE)
        os.mkdir(FAKE_REMOTE_STORAGE)
        print("Reset %s" % FAKE_REMOTE_STORAGE)
        fake_remote_storage = get_remote_path(REMOTE_UNIT_TEST_FOLDER)
        if os.path.isdir(fake_remote_storage):
            shutil.rmtree(fake_remote_storage)
        os.mkdir(fake_remote_storage)
        print("Reset %s" % fake_remote_storage)

    # Overload some config fields if solicited
    original_config = local.load_config()
    local_folder = "%s/.unit_tests/" % original_config['local_root']
    test_config = {
        'DROPBOX_TOKEN': original_config['DROPBOX_TOKEN'],
        'backend_name': original_config['backend_name'],
        'cache': {},
        'local_root': local_folder,
        'path_hashes': {},
        'remote_root': None, 
        'remove_local': False
    }

    # Local storage
    if os.path.isdir(local_folder):
        shutil.rmtree(local_folder)
        print("Reset %s" % local_folder)
    local_storage = local.get_local_file(REMOTE_UNIT_TEST_FOLDER)
    if os.path.isdir(local_storage):
        shutil.rmtree(local_storage)
        print("Reset %s" % local_storage)

    if config_delta:
        for key, value in config_delta.items():
            test_config[key] = value

    # Overload config 
    unit_test_config = "%s/%s" % (
        UNIT_TEST_FOLDER,
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
    fake_remote_storage = get_remote_path(REMOTE_UNIT_TEST_FOLDER)
    local_storage = local.get_local_file(REMOTE_UNIT_TEST_FOLDER)
    if os.path.isdir(fake_remote_storage):
        shutil.rmtree(fake_remote_storage)
    if os.path.isdir(local_storage):
        shutil.rmtree(local_storage)
    unit_test_config = "%s/%s" % (
        UNIT_TEST_FOLDER,
        os.path.basename(local.CONFIG_FILE)
    )
    os.remove(unit_test_config) 
    if sucess:
        print("Test was %s" % green("OK"))
