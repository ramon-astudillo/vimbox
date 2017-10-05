import os
import urllib2
from subprocess import call
#
import envfile
import dropbox
from requests.exceptions import ConnectionError
from dropbox.exceptions import ApiError
from dropbox.files import WriteMode

REMOTE_ROOT = None
ROOT_FOLDER = os.path.realpath("%s/../" % os.path.dirname(__file__))
CONFIG = envfile.load(file_path='%s/.env' % ROOT_FOLDER)
DROPBOX_CLIENT = dropbox.Dropbox(CONFIG['DROPBOX_TOKEN'])

DATA_FOLDER = '%s/DATA' % ROOT_FOLDER

try:
    user_account = DROPBOX_CLIENT.users_get_current_account()
    offline = True
except:
    offline = False


def online():
    try:
        urllib2.urlopen('http://216.58.192.142', timeout=1)
        return True
    except urllib2.URLError as _:
        return False


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


def edit(document_path):
    """
    Edit or create existing file

    Edits will happen on a local copy that will be uploded when finished.
    """

    # Name of the remote file
    if REMOTE_ROOT:
        remote_file = '%s/%s' % (REMOTE_ROOT, document_path)
    else:
        remote_file = '/%s' % document_path

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

    old_local_file = None
    if local_content and remote_content and (local_content != remote_content):

        # Store content on temporary files
        old_local_file = "%s.OLD" % local_file
        write_file(old_local_file, local_content)
        write_file(local_file, remote_content)

        # Show content conflict with vimdiff
        print(" ".join(['vimdimf', '%s %s' % (old_local_file, local_file)]))
        call(['vimdiff', old_local_file, local_file])

    elif remote_content:

        # Fill in local copy with remote content
        write_file(local_file, remote_content)
        print(" ".join(['vim', '%s' % local_file]))
        call(['vim', '%s' % local_file])

    else:

        # New local file
        print(" ".join(['vim', '%s' % local_file]))
        call(['vim', '%s' % local_file])

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
        if os.path.isfile(local_file):
            os.remove(local_file)
        if old_local_file and os.path.isfile(old_local_file):
            os.remove(old_local_file)

    except ApiError as _:

        if online:
            # File non-existing or unreachable
            print("Connection lost keeping local copy in %s" % local_file)
