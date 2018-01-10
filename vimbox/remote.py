"""
Contains remote primitives indepenedent of back-end used and back-end switch

Handles back-end errors in a unified way
"""
import os
import getpass
#
from requests.exceptions import ConnectionError
import dropbox
from dropbox.exceptions import ApiError
from dropbox.files import WriteMode
#
import local
import crypto
import diogenes


# Bash font styles
red = diogenes.style(font_color='light red')
yellow = diogenes.style(font_color='yellow')
green = diogenes.style(font_color='light green')


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


def install_backend():

    if os.path.isfile(local.CONFIG_FILE):
        config = local.read_config(local.CONFIG_FILE)
        if 'DROPBOX_TOKEN' in config:
            print("Found valid config in %s" % local.CONFIG_FILE)

    else:

        # Prompt user for a token
        print(
            "\nI need you to create a dropbox app and give me an acess token."
            "Go here \n\nhttps://www.dropbox.com/developers/apps/\n\n"
            "1) Select Dropbox API\n"
            "2) Select either App folder or Full Dropbox\n"
            "3) Name is irrelevant but vimbox may help you remember\n"
        )
        dropbox_token = raw_input("Push \"generate acess token\" to get one"
                                  " and paste it here: ")
        dropbox_client = dropbox.Dropbox(dropbox_token)

        # Validate token by connecting to dropbox
        user_acount, error = get_user_account(dropbox_client)
        if user_acount is None:
            print("Could not connect to dropbox %s" % error)
            exit(1)
        else:

            print("Connected to dropbox account %s (%s)" % (
                user_acount.name.display_name,
                user_acount.email)
            )
            # Store
            config = local.DEFAULT_CONFIG
            config['DROPBOX_TOKEN'] = dropbox_token
            local.write_config(local.CONFIG_FILE, config)
            print("Created config in %s" % local.CONFIG_FILE)


def get_client(config):

    # TODO: Add here switch to other clients
    # Basic conection check
    if config.get('DROPBOX_TOKEN', None) is None:
        install_backend(config)

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
        config = local.load_config()

    # Get client
    if dropbox_client is None:
        dropbox_client = get_client(config)

    # If encrypted get encrypted remote-name
    if password is not None:
        # Hash filename
        remote_file_hash = crypto.get_path_hash(remote_file)
        # Encript content
        new_local_content = crypto.encrypt_content(new_local_content, password)
    else:
        remote_file_hash = remote_file

    try:

        # Upload file to the server
        dropbox_client.files_upload(
            new_local_content,
            remote_file_hash,
            mode=WriteMode('overwrite')
        )
        error = None

    except ConnectionError:

        # File non-existing or unreachable
        error = 'connection-error'

    except ApiError:

        # File non-existing or unreachable
        error = 'api-error'

    return error


def is_file(remote_file, dropbox_client, config):

    # Hash name if necessary
    is_encrypted = False
    if remote_file in config['path_hashes'].values():
        remote_file = crypto.get_path_hash(remote_file)
        is_encrypted = True

    # Note that with no connection we wont be able to know if the file exists
    try:
        result = dropbox_client.files_alpha_get_metadata(remote_file)
        file_exists = True
    except ConnectionError:
        # This can be missleading
        file_exists = False
    except ApiError:
        if is_encrypted:
            return False
        else:
            # Maybe it is encrypted, but unregistered
            try:
                remote_file = crypto.get_path_hash(remote_file)
                result = dropbox_client.files_alpha_get_metadata(remote_file)
                file_exists = True
                is_encrypted = True
            except ApiError:
                file_exists = False

    return file_exists and hasattr(result, 'content_hash'), is_encrypted


def pull(remote_file, force_creation, config=None, dropbox_client=None,
         password=None):

    # Fetch local content for this file
    local_file, local_content = local.get_local_content(remote_file, config)

    # Fetch remote content for this file
    remote_content, fetch_status = fetch(
        remote_file,
        config=config,
        dropbox_client=dropbox_client,
        password=password,
        is_encrypted=password is not None  # This changes w/ vimbox -x
    )

    # Quick exit on decription failure
    if fetch_status == 'decription-failed':
        print('\nDecription failed check password and vimbox version\n')
        exit(0)

    # Force use of -f to create new folders
    if (
        fetch_status == 'online' and
        remote_content is None and
        not force_creation
    ):
        print('\nYou need to create a file, use -f or -e\n')
        exit(0)

    if remote_content is None:

        # No file in remote (we could be creating one or syncing after offline)
        merged_content = None

    elif local_content is not None and local_content != remote_content:

        # Content conflict, call local.mergetool
        old_local_file = "%s.OLD" % local_file
        local.write_file(old_local_file, local_content)
        local.write_file(local_file, remote_content)
        local.mergetool(old_local_file, local_file)
        merged_content = local.read_file(local_file)
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


def fetch(remote_file, config=None, dropbox_client=None, password=None,
          is_encrypted=False):
    """
    Get local and remote content and coresponding file paths
    """

    # Name of the remote file
    assert remote_file[0] == '/', "Dropbox remote paths start with /"

    # Load config
    if config is None:
        config = local.load_config()

    # Get client
    if dropbox_client is None:
        dropbox_client = get_client(config)

    # If encrypted get encrypted remote-name
    if password or is_encrypted:
        remote_file_hash = crypto.get_path_hash(remote_file)
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

    except ApiError:

        # File non-existing
        remote_content = None
        status = 'online'
        # print("%s does not exist" % (remote_file))

    if remote_content is not None and password is not None:
        remote_content, sucess = crypto.decript_content(
            remote_content, password
        )
        if not sucess:
            status = 'decription-failed'

    return remote_content, status


def get_folders(dropbox_client, remote_folder):

    # Rename '/' to ''
    if remote_folder == '/':
        remote_folder = ''

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

    # NotImplementedYet: Listing of files
    if remote_file and remote_file[-1] != '/':
        print("\nOnly /folders/ can be listed right now\n")
        exit(1)

    # Load config
    if config is None:
        config = local.load_config()

    # Get client
    if dropbox_client is None:
        dropbox_client = get_client(config)

    # Get path hashes
    path_hashes = config['path_hashes']

    # Try first remote
    result, error = get_folders(dropbox_client, remote_file)
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
        # Display encrypted files in red
        new_display_folders = []
        for file_folder in display_folders:
            key = "%s%s" % (remote_file, file_folder)
            if key in path_hashes:
                file_folder = red(os.path.basename(path_hashes[key]))
            new_display_folders.append(file_folder)
        display_string = "".join(
            ["%s\n" % folder for folder in sorted(new_display_folders)]
        )

    elif error == 'api-error':

        display_string = "Folder does not exist in remote!"

    else:

        # If it fails resort to local cache
        display_folders = local.list_local(remote_file, config)
        print("\n%s cache for %s " % (red("offline"), remote_file))
        display_string = "".join(
            ["%s\n" % folder for folder in sorted(display_folders)]
        )

    # Print
    print("\n%s\n" % display_string.rstrip())


def copy(remote_source, remote_target, config=None, dropbox_client=None):

    # Load config if not provided
    if config is None:
        config = local.load_config()

    # Get client if not provided
    if dropbox_client is None:
        dropbox_client = get_client(config)

    # Map `cp /path/to/file /path2/` to `cp /path/to/file /path/file`
    if remote_target[-1] == '/':
        basename = os.path.basename(remote_source)
        remote_target = "%s%s" % (remote_target, basename)
        if remote_source == remote_target:
            print("source and target are the same")
            exit(1)

    # Do not allow to copy on encrypted files
    if (
        remote_source in config['path_hashes'].values() or
        remote_target in config['path_hashes'].values() or
        crypto.is_encrypted_path(remote_target)
    ):
        print("copy/move operations not allowed in encrypted files")
        exit(1)

    sucess = dropbox_client.files_copy_v2(remote_source, remote_target)
    if sucess:
        print("%12s %s %s" % (yellow("copied"), remote_source, remote_target))


def remove(remote_file, config=None, dropbox_client=None, force=False,
           password=None):

    # Load config if not provided
    if config is None:
        config = local.load_config()

    # Get client if not provided
    if dropbox_client is None:
        dropbox_client = get_client(config)

    # Disallow deleting of encrypted files that have unknown name. Also consider
    # the unfrequent file is registered but user uses hash name
    if (
        remote_file not in config['path_hashes'] and
        crypto.is_encrypted_path(remote_file)
    ):
            print("Can not delete uncached encrypted files")
            exit(1)

    # Disallow deleting of folders.
    if not force and not is_file(remote_file, dropbox_client, config)[0]:
        result, error = get_folders(dropbox_client, remote_file)
        if error:
            print("Could not find %s" % remote_file)
            exit(1)

        if result.entries != []:
            print("Can only delete empty folders")
            exit(1)

    # Hash name if necessary
    if remote_file in config['path_hashes'].values():
        original_name = remote_file
        remote_file = crypto.get_path_hash(remote_file)
    else:
        original_name = remote_file

    # TODO: This should go to the client specific part and have exception
    # handling
    if remote_file[-1] == '/':
        # Remove backslash
        # TODO: This is input sanity check should go in the client dependent
        # part
        sucess = dropbox_client.files_delete_v2(remote_file[:-1])
    else:
        sucess = dropbox_client.files_delete_v2(remote_file)

    if sucess:
        print("%12s %s" % (yellow("removed"), original_name))

        # Unregister if it is a folder
        if remote_file[-1] == '/' and remote_file in config['cache']:
            config['cache'].remove(remote_file)
            local.write_config(local.CONFIG_FILE, config)

        # If encrypted remove from path_hashes
        if remote_file in config['path_hashes']:
            del config['path_hashes'][remote_file]
            local.write_config(local.CONFIG_FILE, config)


def edit(remote_file, config=None, dropbox_client=None, remove_local=None,
         diff_mode=False, force_creation=False, register_folder=True,
         password=None):
    """
    Edit or create existing file

    Edits will happen on a local copy that will be uploded when finished.

    remove_local     After sucesful push remove local content
    diff_mode        Only pull and push
    force_creation   Mandatory for new file on remote
    register_folder  Store file path in local cache
    password         Optional encryption/decription on client side
    """

    # Load config if not provided
    if config is None:
        config = local.load_config()
    if remove_local is None:
        remove_local = config['remove_local']

    # Get client if not provided
    if dropbox_client is None:
        dropbox_client = get_client(config)

    # Needed variable names
    local_file = local.get_local_file(remote_file, config)

    # Do basic checks on remote: Does it exist? is it encripted?
    file_exists, is_encrypted = is_file(remote_file, dropbox_client, config)

    # Prompt for password if needed
    if is_encrypted and password is None:
        password = getpass.getpass('Input file password: ')

    # Sanity checks
    # TODO: This has to be cleaner.
    remote_folder = "%s/" % os.path.dirname(remote_file)
    if (
        register_folder and
        os.path.isdir(os.path.dirname(local_file)) and
        remote_folder not in config['cache']
    ):
        print("%s exists localy but is not registered" % remote_folder)

    # If this is a registered encrypted file, we will need a password
    if remote_file in config['path_hashes'].values() and force_creation:
        print('\nCan not re-encrypt a registered file.\n')
        exit()

    if password:
        # If encryption is used we need to register the file in the cache
        if not register_folder:
            print('\nFile encryption only with register_folder = True\n')
            exit()
        password = crypto.validate_password(password)

    if force_creation and file_exists:
        # It can be that the path we want to create uses names that are already
        # files. Here we test this at least one level
        # Quick exit on decription failure
        print('\n%s exists as a file in remote!\n' % remote_file)
        exit(0)

    # fetch remote content, merge if neccesary with local.mergetool
    local_content, remote_content, merged_content, _ = pull(
        remote_file,
        force_creation,
        config=config,
        dropbox_client=dropbox_client,
        password=password
    )

    # Call editor on merged code if solicited
    if diff_mode:
        if remove_local:
            edited_content = merged_content
        else:
            # Dummy no edit, but still makes local copy
            edited_content = local.local_edit(
                local_file,
                merged_content,
                no_edit=True
            )
    else:
        # Edit with edit tool and retieve content
        edited_content = local.local_edit(local_file, merged_content)

    # TODO: Programatic edit operations here

    # Abort if file being created but no changes
    if edited_content is None:
        # For debug purposes
        assert force_creation, \
            "Invalid status: edited local_file non existing but remote does"
        # File creation aborted
        exit()

    # TODO: We would need do a second pull if edit too too much time

    if edited_content != remote_content:

        # Update remote if there are changes

        # Push changes to dropbox
        error = _push(
            edited_content,
            remote_file,
            config,
            dropbox_client,
            password=password
        )

        # Remove local file
        if error is None:

            # Everything went fine
            print("%12s %s" % (yellow("pushed"), remote_file))

            # Register file in cache
            if register_folder:
                # TODO: Right now we only register the folder
                # NOTE: We try this anyaway because of independen hash
                # resgistration
                local.register_file(remote_file, config, password is not None)

            # Remove local copy if solicited
            if remove_local and os.path.isfile(local_file):
                # Remove local file if solicited
                os.remove(local_file)
                print("%12s %s" % (red("cleaned"), local_file))

        elif error == 'connection-error':

            # We are offline. This is a plausible state. Just keep local copy
            # TODO: Course of action if remove_local = True
            print("%12s %s" % (red("offline"), remote_file))
            print("keeping local copy")

            # We do still register the file in cache
            if register_folder:
                # TODO: Right now we only register the folder
                # NOTE: We try this anyaway because of independen hash
                # resgistration
                local.register_file(remote_file, config, password is not None)

        elif error == 'api-error':

            # This is not a normal state. Probably bug on our side or API
            # change/bug on the backend.
            print("%12s %s" % (red("api-error"), remote_file))
            print("API error (something bad happened)")
            print("keeping local copy")

            # Note that we not register file.
            # TODO: How to operate with existing, unregistered files. We only
            # register folder so this is a bit difficult.

        else:

            # This can only be a bug on our side
            raise Exception("Unknown _push error %s" % error)

    elif local_content != remote_content:
        # We overwrote local with remote
        print("%12s %s" % (yellow("pulled"), remote_file))

        # Register file in cache
        if register_folder:
            # TODO: Right now we only register the folder
            # NOTE: We try this anyaway because of independen hash
            # resgistration
            local.register_file(remote_file, config, password is not None)

    else:
        # No changes needed on either side
        print("%12s %s" % (green("in-sync"), remote_file))

        # Register file in cache
        if register_folder:
            # TODO: Right now we only register the folder
            # NOTE: We try this anyaway because of independen hash
            # resgistration
            local.register_file(remote_file, config, password is not None)
