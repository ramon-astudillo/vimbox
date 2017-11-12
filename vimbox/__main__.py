import sys
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
            vimbox.list_folders('/')
        elif len(args) == 2:
            vimbox.list_folders(args[1])
        else:
            vimbox_help()

    else:

        # Multiple arguments
        file_path = None
        force_creation = False
        password = None
        for option in args:
            if option == '-f':
                # Create new file
                force_creation = True
            elif option == '-e':
                # Create new encripted file or register existing one
                force_creation = True
                password = raw_input('Input file password: ')
            elif option[0] == '/':
                # Dropbox path
                file_path = option
            else:
                vimbox_help()

        # Check we got a file path
        if file_path is None:
            vimbox_help()

        # Call edit utility
        vimbox = VimBox()
        vimbox.edit(
            file_path,
            force_creation=force_creation,
            password=password
        )

if __name__ == "__main__":
    main()
