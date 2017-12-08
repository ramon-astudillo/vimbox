import os
import getpass
#
from vimbox.remote import get_client, pull, _push
from vimbox.local import (
    load_config,
    get_local_file,
    register_file,
    local_edit
)
from vimbox.crypto import validate_password
from vimbox.diogenes import style

ROOT_FOLDER = "%s/.vimbox/" % os.environ['HOME']

# Bash font styles
red = style(font_color='light red')
yellow = style(font_color='yellow')
green = style(font_color='light green')


def edit(remote_file, config=None, dropbox_client=None, remove_local=False,
         diff_mode=False, force_creation=False, register_folder=True,
         password=None):
    """
    Edit or create existing file

    Edits will happen on a local copy that will be uploded when finished.

    remove_local     After sucesful push remove local content
    diff_mode        Only pull and push
    force_creation   Mandatory for new file on remote
    register_folder  Store file path in local cache
    password         Optional encription/decription on client side
    """

    # Load config if not provided
    if config is None:
        config = load_config()

    # Get client if not provided
    if dropbox_client is None:
        dropbox_client = get_client(config)

    # If this is a registered encripted file, we will need a password
    if remote_file in config['path_hashes'].values():
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

    # fetch remote content, merge if neccesary with mergetool
    local_content, remote_content, merged_content, online = pull(
        remote_file,
        force_creation,
        config=config,
        dropbox_client=dropbox_client,
        password=password
    )

    # Call editor on merged code if solicited
    if diff_mode:
        edited_content = merged_content
    else:
        # Edit with edit tool and retieve content
        local_file = get_local_file(remote_file, config)
        edited_content = local_edit(local_file, merged_content)

    # TODO: Programatic edit operations here

    # Abort if file being created but no changes
    if edited_content is None:
        # For debug purposes
        assert force_creation, \
            "Invalid status: edited local_file non existing but remote does"
        # File creation aborted
        exit()

    # Register file in cache
    if register_folder:
        register_file(remote_file, config, password=password)

    # TODO: We would need to check for a second merge need if it took lot of
    # time

    # Update remote if there are changes
    if edited_content != remote_content:

        # After edit, changes in the remote needed
        if not online:
            # TODO: Course of action if remove_local = True
            print("%12s %s" % (red("offline"), remote_file))
        else:
            # Push changes to dropbox
            sucess = _push(
                edited_content,
                remote_file,
                config,
                dropbox_client,
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
                # TODO: Course of action if remove_local = True
                print("%12s %s" % (red("offline!?"), remote_file))

    elif local_content != remote_content:
        # We had to update local to match remote (only pull need for sync)
        print("%12s %s" % (yellow("pulled"), remote_file))
    else:
        # No changes needed on either side
        print("%12s %s" % (green("in-sync"), remote_file))
