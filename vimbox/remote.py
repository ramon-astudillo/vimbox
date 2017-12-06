import os
#
from requests.exceptions import ConnectionError
import dropbox
from dropbox.exceptions import ApiError
from dropbox.files import WriteMode
#
from vimbox.local import (
    load_config,
    get_local_content,
    write_file,
    read_file,
    write_config,
    mergetool
)
from vimbox.crypto import get_path_hash, encript_content, decript_content
from vimbox.diogenes import style


ROOT_FOLDER = "%s/.vimbox/" % os.environ['HOME']
CONFIG_FILE = '%s/config.yml' % ROOT_FOLDER


# Bash font styles
red = style(font_color='light red')


def get_user_account(dropbox_client):
    try:

        # Get user info to validate account
        user = dropbox_client.users_get_current_account()
        error = None

    except ConnectionError:

        # Dropbox unrechable
        user = None
        error = 'connection-error'

    except ApiError:

        # API error
        user = None
        error = 'api-error'

    return user, error


def get_client(config):

    # Basic conection check
    if config.get('DROPBOX_TOKEN', None) is None:

        # Prompt user for a token
        print(
            "\nA dropbox access token for vimbox is needed, "
            "see\n\nhttps://www.dropbox.com/developers/apps/\n"
        )
        dropbox_token = raw_input('Please provide Dropbox token: ')
        dropbox_client = dropbox.Dropbox(dropbox_token)

        # Validate token by connecting to dropbox
        user_acount, error = get_user_account(dropbox_client)
        if user_acount is None:
            print("Could not connect to dropbox %s" % error)
            exit(1)
        else:
            # Store
            config['DROPBOX_TOKEN'] = dropbox_token
            write_config(CONFIG_FILE, config)
    else:

        # Checking here for dropbox status can make it too slow
        dropbox_client = dropbox.Dropbox(config['DROPBOX_TOKEN'])

    return dropbox_client


def _push(new_local_content, remote_file, config=None, dropbox_client=None,
          password=None):
    """
    Push updates to remote, do local clean-up if necessary
    """

    # Load config
    if config is None:
        config = load_config()

    # Get client
    if dropbox_client is None:
        dropbox_client = get_client(config)

    # If encripted get encripted remote-name
    if password is not None:
        # Hash filename
        remote_file_hash = get_path_hash(remote_file)
        # Encript content
        new_local_content = encript_content(new_local_content, password)
    else:
        remote_file_hash = remote_file

    try:

        # Upload file to the server
        dropbox_client.files_upload(
            new_local_content,
            remote_file_hash,
            mode=WriteMode('overwrite')
        )
        return True

    except ConnectionError:

        # File non-existing or unreachable
        print("Connection lost keeping local copy")
        return False

    except ApiError:

        # File non-existing or unreachable
        print("API error keeping local copy")
        return False


def pull(remote_file, force_creation, config=None, dropbox_client=None,
         password=None):

    # Fetch local content for this file
    local_file, local_content = get_local_content(remote_file, config)

    # Fetch remote content for this file
    remote_content, fetch_status = fetch(
        remote_file,
        config=config,
        dropbox_client=dropbox_client,
        password=password
    )

    # Quick exit on decription failure
    if fetch_status == 'decription-failed':
        print('\nDecription failed check password and vimbox version\n')
        exit(0)

    # Force use of -f to create new folders
    if remote_content is None and not force_creation:
        print('\nYou need to create a file, use -f or -e\n')
        exit(0)

    if remote_content is None:

        # No file in remote (we could be creating one or syncing after offline)
        merged_content = None

    elif local_content is not None and local_content != remote_content:

        # Content conflict, call mergetool
        old_local_file = "%s.OLD" % local_file
        write_file(old_local_file, local_content)
        write_file(local_file, remote_content)
        mergetool(old_local_file, local_file)
        merged_content = read_file(local_file)
        # Clean up extra temporary file
        os.remove(old_local_file)

    else:

        # No local content, or local matches remote
        merged_content = remote_content

    # Provide status of operation
    if fetch_status != 'online':
        # Copy fetch error
        online = False
    else:
        online = True

    return local_content, remote_content, merged_content, online


def fetch(remote_file, config=None, dropbox_client=None, password=None):
    """
    Get local and remote content and coresponding file paths
    """

    # Name of the remote file
    assert remote_file[0] == '/', "Dropbox remote paths start with /"

    # Load config
    if config is None:
        config = load_config()

    # Get client
    if dropbox_client is None:
        dropbox_client = get_client(config)

    # If encripted get encripted remote-name
    if password:
        remote_file_hash = get_path_hash(remote_file)
    else:
        remote_file_hash = remote_file

    try:

        # Look for remote file, store content
        metadata, response = dropbox_client.files_download(
            remote_file_hash
        )
        remote_content = response.content
        status = 'online'

    except ConnectionError:

        # Dropbox unrechable
        remote_content = None
        status = 'connection-failed'
        print("Can not connect. Working locally")

    except ApiError:

        # File non-existing
        remote_content = None
        status = 'online'
        # print("%s does not exist" % (remote_file))

    if remote_content is not None and password is not None:
        remote_content, sucess = decript_content(remote_content, password)
        if not sucess:
            status = 'decription-failed'

    return remote_content, status


def get_folders(dropbox_client, remote_folder):
    try:

        # Get user info to validate account
        result = dropbox_client.files_list_folder(remote_folder)
        error = None

    except ConnectionError:

        # Dropbox unrechable
        result = None
        error = 'connection-error'

    except ApiError:

        # API error
        result = None
        error = 'api-error'

    return result, error


def list_folders(remote_file, config=None, dropbox_client=None):

    # Load config
    if config is None:
        config = load_config()

    # Get client
    if dropbox_client is None:
        dropbox_client = get_client(config)

    # Get path hashes
    path_hashes = config['path_hashes']

    # Try first remote
    result, _ = get_folders(dropbox_client, remote_file)
    if result:
        # Differentiate file and folders
        display_folders = []
        for x in result.entries:
            if hasattr(x, 'content_hash'):
                # File
                display_folders.append(x.name)
            else:
                # Folder
                display_folders.append("%s/" % x.name)
        display_folders = sorted(display_folders)
        # Display encripted files in red
        new_display_folders = []
        for file_folder in display_folders:
            key = "%s%s" % (remote_file, file_folder)
            if key in path_hashes:
                file_folder = red(os.path.basename(path_hashes[key]))
            new_display_folders.append(file_folder)
        display_folders = new_display_folders

    else:

        # If it fails resort to local cache
        folders = list(set([os.path.dirname(path) for path in config['cache']]))
        offset = len(remote_file)
        display_folders = set()
        for folder in folders:
            if folder[:offset] == remote_file:
                display_folders |= set([folder[offset:].split('/')[0]])
        display_folders = sorted(display_folders)
        if display_folders:
            print("\nOffline, showing cached files/folders")
        # Display encripted files in red
        new_display_folders = []
        for file_folder in display_folders:
            key = file_folder
            if key in path_hashes:
                file_folder = red(key)
            new_display_folders.append(os.path.basename(file_folder) + '/')
        display_folders = new_display_folders

    # Print
    print("")
    for folder in sorted(display_folders):
        print("%s" % folder)
    print("")
