import sys
import os
import getpass
from vimbox.remote import list_folders, copy, remove, install_backend
from vimbox.local import (
    edit_config,
    get_cache,
    get_complete_arguments,
    load_config,
    ROOT_FOLDER,
    modify_bashrc,
    local_install_check
)
# TODO: This should end up in remote
from vimbox import edit


def install():

    # Check if we are in virtual environment
    virtualenv = False
    if hasattr(sys, 'real_prefix'):
        virtualenv = True
        print("\nVirtual environment detected: %s" % sys.prefix)
        print("Config files and bash autocomplete will be installed inside")

    # Create config folder
    if not os.path.isdir(ROOT_FOLDER):
        os.mkdir(ROOT_FOLDER)
        print("Created %s" % ROOT_FOLDER)

    # Configure back-end
    install_backend()

    # Modify bashrc
    modify_bashrc(virtualenv)

    print("vimbox installed sucessfully")

def vimbox_help():
    print("\nvimbox [-f -e ls config] /path/to/file\n")
    exit()

def main(args=None):
    """
    This is refered as vimbox in setup.py
    """

    # From command line
    if args is None:
        args = sys.argv[1:]

    if len(args) == 0:
        vimbox_help()
        exit(1)

    # Sanity check: back-end is installed
    if args[0] not in ['setup', 'complete']:
        local_install_check()

    if args[0] == 'setup':

        install()

    elif args[0] == 'complete':

        for autocomplete_option in get_complete_arguments():
            print(autocomplete_option)

    elif args[0] == 'cache':

        for cached_file in get_cache():
            print(cached_file)

    elif args[0] == 'config':

        edit_config()

    elif args[0] == 'ls':

        if len(args) == 1:
            list_folders('')
        elif len(args) == 2:
            list_folders(args[1])
        else:
            vimbox_help()

    elif args[0] == 'cp':

        if len(args) == 3:
            copy(args[1], args[2])
        else:
            vimbox_help()

    elif args[0] == 'rm':

        if len(args) == 2:
            remove(args[1], force=False)
        elif len(args) == 3 and args[1] == '-R':
            remove(args[2], force=True)
        else:
            vimbox_help()

    elif args[0] == 'mv':

        if len(args) == 3:
            copy(args[1], args[2])
            remove(args[1], force=True)
        else:
            vimbox_help()

    else:

        # Edit / ls alias
        remote_file = None
        force_creation = False
        encript = False
        for option in args:
            if option == '-f':
                # Create new file
                force_creation = True
            elif option == '-e':
                # Create new encripted file
                force_creation = True
                encript = True
            elif option[0] == '/':
                # Dropbox path
                remote_file = option
            else:
                vimbox_help()

        # Check we got a file path
        if remote_file is None:
            vimbox_help()

        # Quick exit: edit file is a folder
        if remote_file[-1] == '/':
            if encript:
                print('\nOnly files can be encripted\n')
            else:
                list_folders(remote_file)
        else:

            # Get config
            config = load_config()

            # Create new encripted file or register existing one
            if encript:

                # Check if file in cache already
                if remote_file in config['path_hashes'].values():
                    print('\nCan not re-encript a registered file.\n')
                    exit()

                # Prompt for password
                password = getpass.getpass('Input file password: ')
                password2 = getpass.getpass('Repeat file password: ')
                if password != password2:
                    print("Passwords do not match!")
                    exit()

            else:
                password = None

            edit(
                remote_file,
                force_creation=force_creation,
                password=password,
                config=config
            )

if __name__ == "__main__":
    main()
