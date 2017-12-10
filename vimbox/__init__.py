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
    password         Optional encription/decription on client side
    """

    # Load config if not provided
    if config is None:
        config = load_config()
    if remove_local is None:
        remove_local = config['remove_local']

    # Get client if not provided
    if dropbox_client is None:
        dropbox_client = get_client(config)

    # Needed variable names
    local_file = get_local_file(remote_file, config)
    local_folder = os.path.dirname(local_file)
    remote_folder = "%s/" % os.path.dirname(remote_file)

    # NotImplemented: I have not found a way to create folders on the root
    creating_folder_on_root = (
        remote_folder not in config['cache'] and 
        len(remote_folder.split('/')) < 3
    )
    if creating_folder_on_root: 
        print(
            "%s trying to create folder on the root. Right now this yields"
            "api-error if it does not exist." % yellow("FIXME")
        )

    # TODO: This has to be cleaner. It is waiting a hardening of the registry
    # process (cache and hash list)
    # Local folder exists but it is not registered. This can only originate
    # from an invalid state exit
    if (
        register_folder and 
        os.path.isdir(local_folder) and 
        remote_folder not in config['cache']
    ):
        print("%s exists localy but is not registered" % remote_folder)

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
    local_content, remote_content, merged_content, _ = pull(
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
        edited_content = local_edit(local_file, merged_content)

    # TODO: Programatic edit operations here

    # Abort if file being created but no changes
    if edited_content is None:
        # For debug purposes
        assert force_creation, \
            "Invalid status: edited local_file non existing but remote does"
        # File creation aborted
        exit()

    # TODO: We would need do a second pull if edit too too much time 

    # Update remote if there are changes
    if edited_content != remote_content:

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
                register_file(remote_file, config, password is not None)

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
                register_file(remote_file, config, password is not None)

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
    else:
        # No changes needed on either side
        print("%12s %s" % (green("in-sync"), remote_file))
