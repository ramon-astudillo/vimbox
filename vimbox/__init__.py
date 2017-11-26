import os
from subprocess import call
import getpass
#
import dropbox
from requests.exceptions import ConnectionError
from dropbox.exceptions import ApiError
from dropbox.files import WriteMode
#
from vimbox.diogenes import style
from vimbox.io import read_config, write_config, read_file, write_file
from vimbox.crypto import (
    get_path_hash,
    validate_password,
    encript_content,
    decript_content
)

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


# Bash font styles
red = style(font_color='red')
yellow = style(font_color='yellow')
green = style(font_color='light green')


def set_autocomplete():
    raise NotImplementedError("Not working at the moment")
    call(['complete -W \"%s\" \'vimbox\'' % get_cache()])


def get_cache():
    config = read_config(CONFIG_FILE)
    return ['config', 'ls'] + config['cache']


def vim_edit_config():
    print(" ".join(['vim', CONFIG_FILE]))
    call(['vim', CONFIG_FILE])
    exit()


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


def vim_merge(local_content, remote_content, tmp_file, diff_mode=False):
    """
    Merge local and remote texts using vim
    """

    old_tmp_file = None
    if local_content and remote_content:

        # There is both local and remote content

        if (local_content != remote_content):

            # They differ

            # Store content on temporary files
            old_tmp_file = "%s.OLD" % tmp_file
            write_file(old_tmp_file, local_content)
            write_file(tmp_file, remote_content)

            # Show content conflict with vimdiff
            print(" ".join([
                'vimdimf', '%s %s' % (old_tmp_file, tmp_file)
            ]))
            call(['vimdiff', old_tmp_file, tmp_file])

        elif not diff_mode:

            # They are the same, we edit the local copy if not in diff mode
            print(" ".join(['vim', '%s' % tmp_file]))
            call(['vim', '%s' % tmp_file])

    elif remote_content:

        # There is only remote content, fill in local copy with remote content.
        # If not in diff mode, also open for editing
        write_file(tmp_file, remote_content)
        if not diff_mode:
            print(" ".join(['vim', '%s' % tmp_file]))
            call(['vim', '%s' % tmp_file])

    elif not diff_mode:

        # There is only local content. If not in diff mode, open for editing
        print(" ".join(['vim', '%s' % tmp_file]))
        call(['vim', '%s' % tmp_file])

    # Read content of edited file
    # NOTE: Than in the last of options above, we might not create a file at all
    if os.path.isfile(tmp_file):
        new_local_content = read_file(tmp_file)
    else:
        new_local_content = None

    # Clean up extra temporary files
    if old_tmp_file and os.path.isfile(old_tmp_file):
        os.remove(old_tmp_file)

    return new_local_content


#
# CLASS
#

class VimBox():

    def __init__(self):

        # Create vimbox folder
        if not os.path.isdir(ROOT_FOLDER):
            os.mkdir(ROOT_FOLDER)
            print("Created %s" % ROOT_FOLDER)

        # Create vimbox config
        if os.path.isfile(CONFIG_FILE):
            self.config = read_config(CONFIG_FILE)
            # Check current defaults are present (version missmatch)
            if set(self.config.keys()) < set(DEFAULT_CONFIG.keys()):

                print("Updating config")
                for key, value in DEFAULT_CONFIG.items():
                    if key not in self.config:
                        print("%s = %s" % (key, value))
                        self.config[key] = value
                # Update config
                write_config(CONFIG_FILE, self.config)

            elif set(self.config.keys()) > set(DEFAULT_CONFIG.keys()):

                # Extra fields (probably from old versions)
                outdated_fields = (
                    set(self.config.keys()) - set(DEFAULT_CONFIG.keys())
                )
                if outdated_fields:
                    print(
                        "\nOutdated fields %s, remove with vimbox config\n" %
                        ", ".join(outdated_fields)
                    )

        else:
            # Default config
            self.config = DEFAULT_CONFIG
            write_config(CONFIG_FILE, self.config)
            print("Created %s" % CONFIG_FILE)

        # Basic conection check
        if self.config.get('DROPBOX_TOKEN', None) is None:

            # Prompt user for a token
            print(
                "\nA dropbox access token for vimbox is needed, "
                "see\n\nhttps://www.dropbox.com/developers/apps/\n"
            )
            dropbox_token = raw_input('Please provide Dropbox token: ')
            self.dropbox_client = dropbox.Dropbox(dropbox_token)

            # Validate token by connecting to dropbox
            user_acount, error = get_user_account(self.dropbox_client)
            if user_acount is None:
                print("Could not connect to dropbox %s" % error)
                exit(1)
            else:
                # Store
                self.config['DROPBOX_TOKEN'] = dropbox_token
                write_config(CONFIG_FILE, self.config)
        else:

            # Checking here for dropbox status can make it too slow
            self.dropbox_client = dropbox.Dropbox(self.config['DROPBOX_TOKEN'])

    def list_folders(self, remote_file):

        # Get path hashes
        path_hashes = self.config['path_hashes']

        # Try first remote
        result, _ = get_folders(self.dropbox_client, remote_file)
        if result:
            display_folders = sorted([x.name for x in result.entries])
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
            folders = list(set([
                os.path.dirname(path) for path in self.config['cache']
            ]))
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
                new_display_folders.append(os.path.basename(file_folder))
            display_folders = new_display_folders

        # Print
        print("")
        for folder in sorted(display_folders):
            print("%s" % folder)
        print("")

    def register(self, remote_file, force_creation, password=None):
        """
        A file can be registered by its folder or it name directly
        """

        # Folder path
        remote_folder = '%s/' % os.path.dirname(remote_file)
        is_registered = False
        if remote_folder and remote_folder in self.config['cache']:
            is_registered = True
        elif remote_file in self.config['cache']:
            is_registered = True

        # Force use of -f to create new folders
        if not is_registered:
            if not force_creation:
                print('\nYou need to create a file, use -f or -e\n')
                exit(1)
            else:
                self.config['cache'].append(remote_folder)
                write_config(CONFIG_FILE, self.config)
                print("Added %s" % remote_folder)
                # Update autocomplete options
                # set_autocomplete()

        # Register file hash in the local cache
        if password:
            remote_file_hash = get_path_hash(remote_file)
            if remote_file_hash not in self.config['path_hashes']:
                self.config['path_hashes'][remote_file_hash] = remote_file
                write_config(CONFIG_FILE, self.config)

    def get_local_file(self, remote_file):
        return '%s/%s' % (self.config['local_root'], remote_file)

    def edit(self, remote_file, remove_local=False, diff_mode=False,
             force_creation=False, register_folder=True, password=None):
        """
        Edit or create existing file

        Edits will happen on a local copy that will be uploded when finished.

        remove_local    set to remove local file after moving it to remote
        diff_mode       will only edit if both remote and local exist and
                        differ, otherwise it copies one to the other
        """

        # If this is a registered encripted file, we will need a password
        if remote_file in self.config['path_hashes'].values():
            # TODO: Think of improper use of -e the second time
            if force_creation:
                print('\nCan not re-encript a registered file.\n')
                exit()
            if password is None:
                password = getpass.getpass('Input file password: ')

        # Sanity check: validate password
        if password:
            # If encription is used we need to register the file in the cache
            if not register_folder:
                print('\nFile encription only with register_folder = True\n')
                exit()
            password = validate_password(password)

        # Fetch local content for this file
        local_file, local_content = self.get_local_content(remote_file)
        # Fetch remote content for this file
        remote_content, status = self._fetch(remote_file, password=password)
        # Quick exit on decription failure
        if status == 'decription-failed':
            print('\nDecription failed check password and vimbox version\n')
            exit()

        # Register file
        if register_folder:
            self.register(remote_file, force_creation, password=password)

        # Merge content with vim
        merged_content = vim_merge(
            local_content,
            remote_content,
            local_file,
            diff_mode=diff_mode
        )

        # Update remote if there are changes
        if merged_content != remote_content:

            # After edit, changes in the remote needed
            if status == 'connection-failed':
                print("%12s %s" % (red("offline"), remote_file))
            else:
                # Push changes to dropbox
                sucess = self._push(
                    merged_content,
                    remote_file,
                    password=password
                )
                # Remove local file
                if sucess:
                    print("%12s %s" % (yellow("pushed"), remote_file))
                    if remove_local and os.path.isfile(local_file):
                        # Remove local file if solicited
                        os.remove(local_file)
                        print("%12s %s" % (red("cleaned"), local_file))
                else:
                    print("%12s %s" % (red("offline?"), remote_file))

        elif local_content != remote_content:
            # We had to update local to match remote
            print("%12s %s" % (yellow("pulled"), remote_file))
        else:
            # No changes needed on either side
            print("%12s %s" % (green("in-sync"), remote_file))

    def get_local_content(self, remote_file):

        # Name of coresponding local file
        local_file = self.get_local_file(remote_file)

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

    def _fetch(self, remote_file, password=None):
        """
        Get local and remote content and coresponding file paths
        """

        # Name of the remote file
        assert remote_file[0] == '/', "Dropbox remote paths start with /"

        # If encripted get encripted remote-name
        if password:
            remote_file_hash = get_path_hash(remote_file)
        else:
            remote_file_hash = remote_file

        try:

            # Look for remote file, store content
            metadata, response = self.dropbox_client.files_download(
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
            status = 'unexisting-file'
            print("%s does not exist" % (remote_file))

        if remote_content is not None and password is not None:
            remote_content, sucess = decript_content(remote_content, password)
            if not sucess:
                status = 'decription-failed'

        return remote_content, status

    def _push(self, new_local_content, remote_file, password=None):
        """
        Push updates to remote, do local clean-up if necessary
        """

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
            self.dropbox_client.files_upload(
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
