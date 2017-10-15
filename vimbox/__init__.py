import os
from subprocess import call
#
import dropbox
from requests.exceptions import ConnectionError
from dropbox.exceptions import ApiError
from dropbox.files import WriteMode
#
from vimbox.io import read_config, write_config, read_file, write_file

ROOT_FOLDER = "%s/.vimbox/" % os.environ['HOME']
CONFIG_FILE = '%s/config.yml' % ROOT_FOLDER

DEFAULT_CONFIG = {
    'DROPBOX_TOKEN': None,
    'local_root': '%s/DATA' % ROOT_FOLDER,
    'remote_root': None,
    'remote_folders': []
}


def set_autocomplete():
    raise NotImplementedError("Not working at the moment")
    call(['complete -W \"%s\" \'vimbox\'' % folders()])


def folders():
    config = read_config(CONFIG_FILE)
    return config['remote_folders']


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
            if set(self.config.keys()) != set(DEFAULT_CONFIG.keys()):
                print("Updating config")
                for key, value in DEFAULT_CONFIG.items():
                    if key not in self.config:
                        print("%s = %s" % (key, value))
                        self.config[key] = value
                # Update config
                write_config(CONFIG_FILE, self.config)
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
            # Validate token by connecting to dropbox
            self.dropbox_client = dropbox.Dropbox(dropbox_token)
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

    def edit(self, remote_file, remove_local=False, diff_mode=False,
             force_creation=False, register_folder=True):
        """
        Edit or create existing file

        Edits will happen on a local copy that will be uploded when finished.

        remove_local    set to remove local file after moving it to remote
        diff_mode       will only edit if both remote and local exist and
                        differ, otherwise it copies one to the other
        """

        # Quick exit: edit file is not a file but a look like a folder
        if remote_file[-1] == '/':
            print("")
            result = self.dropbox_client.files_list_folder(remote_file)
            for entry in result.entries:
                print entry.name
            print("")
            exit(0)

        # Fetch local and remote copies for the file. This may not exist or be
        # in conflict
        local_file, local_content, remote_content, online = \
            self._fetch_file(remote_file)

        # Make local folder if it does not exist
        local_folder = os.path.dirname(local_file)
        if not os.path.isdir(local_folder):
            os.makedirs(local_folder)
        # Force use of -f to create new files
        if (
            not force_creation and
            remote_content is None and online
        ):
            print('\nYou are creating a new file, use -f\n')
            exit(1)
        # Force use of -f to create new folders
        remote_folder = '%s/' % os.path.dirname(remote_file)
        if (
            not force_creation and
            remote_folder and
            remote_folder not in self.config['remote_folders']
        ):
            print('\nYou need to create a folder, use -f\n')
            exit(1)

        # Add remote folder to list
        if (
            remote_folder not in self.config['remote_folders'] and
            register_folder
        ):
            print("Added %s" % remote_folder)
            self.config['remote_folders'].append(remote_folder)
            write_config(CONFIG_FILE, self.config)
            # Update autocomplete options
            # set_autocomplete()

        # Merge content with vim
        merged_content = vim_merge(
            local_content, remote_content, local_file, diff_mode=diff_mode
        )

        # Update remote if there are changes
        if not online:
            print("Offline, will upload in next edit")

        elif merged_content != remote_content:

            # Push changes to dropbox
            sucess = self._push(merged_content, remote_file)

            # Remove local file
            if sucess and remove_local and os.path.isfile(local_file):
                os.remove(local_file)
                print("Removed %s" % local_file)

        else:
            print("No update of remote needed")

    def _fetch_file(self, remote_file):
        """
        Get local and remote content and coresponding file paths
        """

        # Name of the remote file
        assert remote_file[0] == '/', "Dropbox remote paths start with /"

        # Name of coresponding local file
        local_file = '%s/%s' % (self.config['local_root'], remote_file)
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

        online = True
        try:

            # Look for remote file, store content
            metadata, response = self.dropbox_client.files_download(remote_file)
            remote_content = response.content

        except ConnectionError:

            # Dropbox unrechable
            remote_content = None
            online = False
            print("Can not connect. Working locally on %s" % (local_file))

        except ApiError:

            # File non-existing
            remote_content = None
            print("%s does not exist" % (remote_file))

        return local_file, local_content, remote_content, online

    def _push(self, new_local_content, remote_file):
        """
        Push updates to remote, do local clean-up if necessary
        """

        try:

            # Upload file to the server
            self.dropbox_client.files_upload(
                new_local_content,
                remote_file,
                mode=WriteMode('overwrite')
            )
            print("Updated in Dropbox %s" % remote_file)
            return True

        except ConnectionError:

            # File non-existing or unreachable
            print("Connection lost keeping local copy")
            return False

        except ApiError:

            # File non-existing or unreachable
            print("API error keeping local copy")
            return False
