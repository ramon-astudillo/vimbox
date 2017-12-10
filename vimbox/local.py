import os
import yaml
from subprocess import call
from vimbox.crypto import get_path_hash
from vimbox.diogenes import style

ROOT_FOLDER = "%s/.vimbox/" % os.environ['HOME']
CONFIG_FILE = '%s/config.yml' % ROOT_FOLDER
DEFAULT_CONFIG = {
    # This will store the dropbox token (no need to add it manually here!)
    'DROPBOX_TOKEN': None,
    # This will be appended to local paths
    'local_root': '%s/DATA' % ROOT_FOLDER,
    # This will be appended to all paths within dropbox
    'remote_root': None,
    # This will store the local cache
    'cache': [],
    # This will store dict() s of hash: file_path for encripted files
    'path_hashes': {}
}
EDITTOOL = 'vim'
MERGETOOL = 'vim'


# Bash font styles
red = style(font_color='light red')


def write_config(file_path, config):
    with open(file_path, 'w') as fid:
        yaml.dump(config, fid, default_flow_style=False)


def read_config(file_path):
    with open(file_path, 'r') as fid:
        config = yaml.load(fid)
    return config


def edit_config():
    edittool(CONFIG_FILE)


def load_config():

    # Create vimbox folder
    if not os.path.isdir(ROOT_FOLDER):
        os.mkdir(ROOT_FOLDER)
        print("Created %s" % ROOT_FOLDER)

    # Create vimbox config
    if os.path.isfile(CONFIG_FILE):
        config = read_config(CONFIG_FILE)
        # Check current defaults are present (version missmatch)
        if set(config.keys()) < set(DEFAULT_CONFIG.keys()):

            print("Updating config")
            for key, value in DEFAULT_CONFIG.items():
                if key not in config:
                    print("%s = %s" % (key, value))
                    config[key] = value
            # Update config
            write_config(CONFIG_FILE, config)

        elif set(config.keys()) > set(DEFAULT_CONFIG.keys()):

            # Extra fields (probably from old versions)
            outdated_fields = (set(config.keys()) - set(DEFAULT_CONFIG.keys()))
            if outdated_fields:
                print(
                    "\nOutdated fields %s, remove with vimbox config\n" %
                    ", ".join(outdated_fields)
                )

    else:
        # Default config
        config = DEFAULT_CONFIG
        write_config(CONFIG_FILE, config)
        print("Created %s" % CONFIG_FILE)

    return config


def get_cache():
    config = read_config(CONFIG_FILE)
    return config['cache']


def get_complete_arguments():
    return ['config', 'ls'] + get_cache()


def register_file(remote_file, config, is_encripted):
    """
    A file can be registered by its folder or it name directly
    """

    # Folder path
    remote_folder = '%s/' % os.path.dirname(remote_file)
    is_registered = False
    if remote_folder and remote_folder in config['cache']:
        is_registered = True
    elif remote_file in config['cache']:
        is_registered = True

    # Register file
    # TODO: Should be after sucesful vim edition
    if not is_registered:
        config['cache'].append(remote_folder)
        write_config(CONFIG_FILE, config)
        print("Added %s" % remote_folder)
        # Update autocomplete options

    # Register file hash in the local cache
    if is_encripted:
        remote_file_hash = get_path_hash(remote_file)
        if remote_file_hash not in config['path_hashes']:
            config['path_hashes'][remote_file_hash] = remote_file
            write_config(CONFIG_FILE, config)


def get_local_file(remote_file, config):
    return '%s/%s' % (config['local_root'], remote_file)


def get_local_content(remote_file, config):

    # Name of coresponding local file
    local_file = get_local_file(remote_file, config)

    # Create local folder if needed
    local_folder = os.path.dirname(local_file)
    if not os.path.isdir(local_folder):
        os.makedirs(local_folder)

    # Look for local content
    if os.path.isfile(local_file):
        # Read local content
        with open(local_file, 'r') as fid_local:
            local_content = fid_local.read()
    else:
        local_content = None

    return local_file, local_content


def write_file(file_path, content):
    with open(file_path, 'w') as fid_local:
        fid_local.write(content)


def read_file(file_path):
    with open(file_path, 'r') as fid_local:
        return fid_local.read()


def mergetool(old_local_file, local_file):
    # Show content conflict with vimdiff
    print(" ".join([MERGETOOL, '%s %s' % (old_local_file, local_file)]))
    call([MERGETOOL, old_local_file, local_file])


def edittool(local_file):
    # call your editor
    print(" ".join([EDITTOOL, '%s' % local_file]))
    call([EDITTOOL, '%s' % local_file])
    # TODO: Check for abnormal termination


def local_edit(local_file, local_content):
    # TODO: Merge this and the above
    if local_content is not None:
        # local_content is None if we start from scratch
        write_file(local_file, local_content)
    edittool(local_file)
    if os.path.isfile(local_file):
        edited_local_content = read_file(local_file)
    else:
        # edited content is None if we start from scratch but do nothing on vim
        edited_local_content = None
    return edited_local_content

def list_local(remote_file, config):

    path_hashes = config['path_hashes']
    folders = list(set([os.path.dirname(path) for path in config['cache']]))
    offset = len(remote_file)
    display_folders = set()
    for folder in folders:
        if folder[:offset] == remote_file:
            display_folders |= set([folder[offset:].split('/')[0]])
    display_folders = sorted(display_folders)
    # Display encripted files in red
    new_display_folders = []
    for file_folder in display_folders:
        key = file_folder
        if key in path_hashes:
            file_folder = red(key)
        new_display_folders.append(os.path.basename(file_folder) + '/')
    return new_display_folders
