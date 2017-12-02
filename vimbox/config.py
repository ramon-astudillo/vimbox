import os
import yaml
from vimbox.editor import edittool

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
