import os
from subprocess import call
#
import envfile
import dropbox
from requests.exceptions import ConnectionError
from dropbox.exceptions import ApiError
from dropbox.files import WriteMode

REMOTE_ROOT = None
ROOT_FOLDER = "%s/.vimbox/" % os.environ['HOME']
if not os.path.isdir(ROOT_FOLDER):
    print("Created %s" % ROOT_FOLDER)
    os.mkdir(ROOT_FOLDER)
ENV_FILE = '%s/.env' % ROOT_FOLDER

if os.path.isfile(ENV_FILE):
    CONFIG = envfile.load(file_path=ENV_FILE)
    dropbox_token = CONFIG['DROPBOX_TOKEN']
else:
    print("Missing .env file with Dropbox token")
    dropbox_token = raw_input('Please provide Dropbox token: ')
    envfile.save(ENV_FILE, {'DROPBOX_TOKEN': dropbox_token})
    print('.env file saved to %s' % ENV_FILE)

DROPBOX_CLIENT = dropbox.Dropbox(dropbox_token)

DATA_FOLDER = '%s/DATA' % ROOT_FOLDER

try:
    user_account = DROPBOX_CLIENT.users_get_current_account()
    offline = True
except:
    offline = False


def exists(path):
    try:
        DROPBOX_CLIENT.files_get_metadata(path)
        return True
    except:
        return False


def write_file(file_path, content):
    with open(file_path, 'w') as fid_local:
        fid_local.write(content)


def read_file(file_path):
    with open(file_path, 'r') as fid_local:
        return fid_local.read()


def get_content(document_path):

    # Name of the remote file
    assert document_path[0] == '/', "Dropbox paths start with /"
    remote_file = '%s' % document_path

    # Name of coresponding local file
    local_file = '%s/%s' % (DATA_FOLDER, document_path)
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

    try:

        # Look for remote file, store content
        metadata, res_progress = DROPBOX_CLIENT.files_download(remote_file)
        remote_content = res_progress.content
        online = True

    except ConnectionError as _:

        # Dropbox unrechable
        remote_content = None
        online = False
        print("Can not connect. Working locally on %s" % (local_file))

    except ApiError as _:

        # File non-existing
        print("%s does not exist" % (remote_file))
        online = True
        remote_content = None

    return local_file, local_content, remote_file, remote_content


def edit(document_path, remove_local=False, diff_mode=True):
    """
    Edit or create existing file

    Edits will happen on a local copy that will be uploded when finished.

    remove_local    set to remove local file after moving it to remote
    diff_mode       will only edit if both remote and local exist and differ,
                    otherwise it copies one to the other
    """

    items = get_content(document_path)
    local_file, local_content, remote_file, remote_content = items

    old_local_file = None
    if local_content and remote_content:

        # There is both local and remote content

        if (local_content != remote_content):

            # They differ

            # Store content on temporary files
            old_local_file = "%s.OLD" % local_file
            write_file(old_local_file, local_content)
            write_file(local_file, remote_content)

            # Show content conflict with vimdiff
            print(" ".join(['vimdimf', '%s %s' % (old_local_file, local_file)]))
            call(['vimdiff', old_local_file, local_file])

        elif not diff_mode:

            # They are the same, we edit the local copy if solicited
            print(" ".join(['vim', '%s' % local_file]))
            call(['vim', '%s' % local_file])

    elif remote_content:

        # Only remote content, fill in local copy with remote content
        write_file(local_file, remote_content)
        if not diff_mode:
            print(" ".join(['vim', '%s' % local_file]))
            call(['vim', '%s' % local_file])

    elif not diff_mode:

        # Only local content, edit it if solicited
        print(" ".join(['vim', '%s' % local_file]))
        call(['vim', '%s' % local_file])

    update_remote(
        remote_file, local_file, old_local_file, remove_local=remove_local
    )


def update_remote(remote_file, local_file, old_local_file, remove_local=False):
    """
    Push updates to remote
    """

    # Read content of edited file
    new_local_content = read_file(local_file)

    try:

        # Upload file to the server
        DROPBOX_CLIENT.files_upload(
            new_local_content,
            remote_file,
            mode=WriteMode('overwrite')
        )
        print("Updated in Dropbox %s" % remote_file)

        # Remove local file
        if remove_local:
            if os.path.isfile(local_file):
                os.remove(local_file)
            if old_local_file and os.path.isfile(old_local_file):
                os.remove(old_local_file)
            print("Removed %s" % local_file)

    except ApiError as _:

        if online:
            # File non-existing or unreachable
            print("Connection lost keeping local copy in %s" % local_file)
