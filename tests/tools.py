import os
import sys
import shutil
from vimbox.diogenes import style
from vimbox import crypto
from vimbox import local
from vimbox.remote.primitives import VimboxClient
from vimbox.remote.fake_backend import get_fake_remote_local_path

green = style(font_color='light green')

# Name of the folder where we carry on the test
if hasattr(sys, 'real_prefix'):
    ROOT_FOLDER = "%s/.vimbox/" % sys.prefix
else:
    ROOT_FOLDER = "%s/.vimbox/" % os.environ['HOME']
# DATA storage for unit test
REMOTE_UNIT_TEST_FOLDER = '/.vimbox_unit_test/'


def is_local_file(file_path):
    local_file = local.get_local_file(file_path)
    return os.path.isfile(local_file)


def is_local_dir(file_path):
    local_file = local.get_local_file(file_path)
    return os.path.isdir(local_file)


def is_fake_remote_file(file_path, password=None):
    if password:
        file_path = crypto.get_path_hash(file_path)
    remote_file = get_fake_remote_local_path(file_path)
    return os.path.isfile(remote_file)


def is_fake_remote_dir(file_path):
    remote_file = get_fake_remote_local_path(file_path)
    return os.path.isdir(remote_file)


def read_file(file_path):
    with open(file_path) as fid:
        return fid.read()


def read_remote_content(remote_file, password=None):

    if password:
        password = crypto.validate_password(password)
        remote_file = crypto.get_path_hash(remote_file)
        true_path = get_fake_remote_local_path(remote_file)
        with open(true_path, 'rb') as fid:
            text = fid.read()
        text, _ = crypto.decript_content(text, password)
    else:
        true_path = get_fake_remote_local_path(remote_file)
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


def reset_folder(folder_path, delete=False):

    # Local
    local_unit_test_folder = local.get_local_file(REMOTE_UNIT_TEST_FOLDER)
    unit_test_name = os.path.basename(local_unit_test_folder[:-1])
    assert unit_test_name == '.vimbox_unit_test', \
        "unit-test folder changed name. Aborting just in case."

    # Remote
    # NOTE: This assumes these operations pass the unit test!
    client = VimboxClient()
    ret = client.client.file_type(REMOTE_UNIT_TEST_FOLDER[:-1])
    if ret['status'] == 'online' and ret['content'] == 'dir':
        client.client.files_delete(REMOTE_UNIT_TEST_FOLDER[:-1])
        print("Removed %s" % REMOTE_UNIT_TEST_FOLDER)
    if os.path.isdir(local_unit_test_folder):
        shutil.rmtree(local_unit_test_folder)
    if not delete:
        client.client.make_directory(REMOTE_UNIT_TEST_FOLDER[:-1])
        os.mkdir(local_unit_test_folder)


def write_remote_content(remote_file, remote_content):

    # FIXME: This function does not exist
    true_path = local.get_remote_path(remote_file)

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

    # Overload some config fields if solicited
    original_config = local.load_config()
    test_config = {
        'DROPBOX_TOKEN': original_config['DROPBOX_TOKEN'],
        'backend_name': original_config['backend_name'],
        'cache': {},
        'path_hashes': {},
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

    # Remote storage
    backend_name = config_delta.get('backend_name', None)
    assert REMOTE_UNIT_TEST_FOLDER[:-1] == '/.vimbox_unit_test', \
        "CHANGING UNIT TEST FOLDER CAN LEAD TO DATA LOSS"
    reset_folder(REMOTE_UNIT_TEST_FOLDER)

    return unit_test_config


def reset_environment(sucess=False):
    """
    - Remove folder simulating storage in remote
    - Remove folder in the local vimbox cache (THIS IS THE ACTUAL CACHE)
    - keep original config to restore it later
    """
    # Local storage
    test_config = local.load_config()
    reset_folder(REMOTE_UNIT_TEST_FOLDER, delete=True)
    # Extra check
    assert os.path.basename(local.CONFIG_FILE) == 'unit_test_config.yml', \
        "unit test configurstion has unexpected name, not deleting it"
    os.remove(local.CONFIG_FILE)
    print("Removing config %s" % local.CONFIG_FILE)

    # Inform user
    if sucess:
        print("Test was %s" % green("OK"))


def run_in_environment(test_function, backend_name='fake', debug=False):

    if debug:
        start_environment(backend_name=backend_name)
        test_function()
        reset_environment(sucess=True)

    else:
        try:
            start_environment(backend_name=backend_name)
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
