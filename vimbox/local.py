import os
import sys
import yaml
from subprocess import call
# vimbox modules
import crypto
import diogenes

# Locate the vimbox config. If we are inside a virtual environment look for it
# inside
if hasattr(sys, 'real_prefix'):
    ROOT_FOLDER = "%s/.vimbox/" % sys.prefix
else:
    ROOT_FOLDER = "%s/.vimbox/" % os.environ['HOME']
CONFIG_FILE = '%s/config.yml' % ROOT_FOLDER
# Flag to indicate if it is installed
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
    'path_hashes': {},
    # By default remove all synced files
    'remove_local': False
}
EDITTOOL = 'vim'
MERGETOOL = 'vimdiff'


# Bash font styles
red = diogenes.style(font_color='light red')


def modify_bashrc(virtualenv):
    """Adds complete -W command to bashrc or activate in a virtualenv"""

    if virtualenv and os.path.isfile("%s/bin/activate" % sys.prefix):
        bashrc = "%s/bin/activate" % sys.prefix
    else:
        bashrc = "%s/.bashrc" % os.environ['HOME']

    # Add complete line for bashrc
    complete_string = "complete -W \"$(vimbox complete)\" \'vimbox\'\n"
    if os.path.isfile(bashrc):
        with open(bashrc, 'r') as fid:
            lines = fid.readlines()
        if complete_string not in lines:
            with open(bashrc, 'a') as fid:
                fid.write('\n# Argument completion for vimbox\n')
                fid.write(complete_string)
                print("Added complete to %s" % bashrc)

    else:
        with open(bashrc, 'w') as fid:
            fid.write('\n# Argument completion for vimbox\n')
            fid.write(complete_string)
            print("Created %s" % bashrc)


def write_config(file_path, config):
    with open(file_path, 'w') as fid:
        yaml.dump(config, fid, default_flow_style=False)


def read_config(file_path):
    with open(file_path, 'r') as fid:
        config = yaml.load(fid)
    return config


def edit_config():
    edittool(CONFIG_FILE)


def local_install_check():
    if not os.path.isfile(CONFIG_FILE):
        print("Missing config in %s" % CONFIG_FILE)
        print("Run vimbox setup")
        exit(1)


def load_config():

    # Create vimbox config
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

    return config


def get_cache():
    # note that we do not use load_config here on purpose. If instalation failed
    # this will be called in .bashrc to set arguments. It is safer to return
    # empty directly that having any code running.
    if os.path.isfile(CONFIG_FILE):
        config = read_config(CONFIG_FILE)
        return config['cache']
    else:
        return []


def get_complete_arguments():
    return ['setup', 'cache', 'config', 'ls', 'cp', 'mv', 'rm'] + get_cache()


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
        remote_file_hash = crypto.get_path_hash(remote_file)
        if remote_file_hash not in config['path_hashes']:
            config['path_hashes'][remote_file_hash] = remote_file
            write_config(CONFIG_FILE, config)


def get_local_file(remote_file, config=None):

    if config is None:
        config = load_config()

    if remote_file in config['path_hashes'].values():
        remote_file = crypto.get_path_hash(remote_file)
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


def local_edit(local_file, local_content, no_edit=False):
    # TODO: Merge this and the above
    if local_content is not None:
        # local_content is None if we start from scratch
        write_file(local_file, local_content)

    if not no_edit:
        edittool(local_file)
        if os.path.isfile(local_file):
            edited_local_content = read_file(local_file)
        else:
            # edited content is None if we start from scratch but do nothing on
            # vim
            edited_local_content = None
    else:
        edited_local_content = local_content

    return edited_local_content


def list_local(remote_file, config):

    path_hashes = config['path_hashes']

    if config.get('remove_local', False):
        # There is no local files, so just use the cache
        folders = list(set([os.path.dirname(path) for path in config['cache']]))
        offset = len(remote_file)
        display_folders = set()
        for folder in folders:
            if folder[:offset] == remote_file:
                display_folders |= set([folder[offset:].split('/')[0]])
        display_folders = sorted(display_folders)
        # As of now cache only contains folders
        are_folder = [True]*len(display_folders)
    else:
        # There are local files, so we can list those
        display_folders = sorted(
            os.listdir(get_local_file(remote_file, config))
        )
        # These can be both files and folders
        are_folder = map(os.path.isdir, [
            get_local_file("%s/%s" % (remote_file, rfile), config)
            for rfile in display_folders
        ])

    new_display_folders = []
    for file_folder, is_folder in zip(display_folders, are_folder):
        if is_folder:
            new_display_folders.append(os.path.basename(file_folder) + '/')
        else:
            if "%s%s" % (remote_file, file_folder) in path_hashes.values():
                # Display encripted files in red
                file_folder = red(file_folder)
            new_display_folders.append(os.path.basename(file_folder))
    return new_display_folders
