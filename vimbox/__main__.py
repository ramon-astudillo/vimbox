import sys
import getpass
from vimbox import VimBox, vim_edit_config, get_cache


def vimbox_help():
    print("\nvimbox [-f] path/to/file\n")
    exit()


def main(args=None):
    """
    This is renamed as vimbox in setup.py
    """

    # From command line
    if args is None:
        args = sys.argv[1:]

    if len(args) == 0:
        vimbox_help()

    elif args[0] == 'cache':

        for cached_file in get_cache():
            print cached_file

    elif args[0] == 'config':

        vim_edit_config()

    elif args[0] == 'ls':

        vimbox = VimBox()
        if len(args) == 1:
            vimbox.list_folders('')
        elif len(args) == 2:
            vimbox.list_folders(args[1])
        else:
            vimbox_help()

    else:

        # Multiple arguments
        remote_file = None
        force_creation = False
        password = None
        for option in args:
            if option == '-f':
                # Create new file
                force_creation = True
            elif option == '-e':
                # Create new encripted file or register existing one
                force_creation = True
                password = getpass.getpass('Input file password: ')
            elif option[0] == '/':
                # Dropbox path
                remote_file = option
            else:
                vimbox_help()

        # Check we got a file path
        if remote_file is None:
            vimbox_help()

        # Call edit utility
        vimbox = VimBox()

        # Quick exit: edit file is a folder
        if remote_file[-1] == '/':
            if password:
                print('\nOnly files can be encripted\n')
            else:
                # TODO: Handle here offline-mode and encripted files
                vimbox.list_folders(remote_file)
        else:
            vimbox.edit(
                remote_file,
                force_creation=force_creation,
                password=password
            )

if __name__ == "__main__":
    main()
