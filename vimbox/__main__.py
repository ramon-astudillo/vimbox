import sys
from vimbox import VimBox, vim_edit_config, folders


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

    # Argument-less options
    if len(args) == 1:

        # Single arguments
        if args[1] == 'config':
            vim_edit_config()
        elif args[1] == 'ls':
            print("")
            for folder in sorted(folders()):
                print(folder)
            print("")
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
