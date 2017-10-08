import sys
from vimbox import VimBox, vim_edit_config


def vimbox_help():
    print("\nvimbox [-f] path/to/file\n")
    exit()


def main(args=None):
    """
    This is renamed as vimbox in setup.py
    """
    if args is None:
        args = sys.argv[1:]

    # Gather options from command line
    file_path = None
    create_folder = False
    edit_config = False
    for option in args:
        if option == '-f':
            create_folder = True
        elif option == '-c':
            edit_config = True
        elif file_path is not None:
            vimbox_help()
        else:
            file_path = option
    if file_path is None and not edit_config:
        vimbox_help()

    # Simple edit config mode
    if edit_config:
        vim_edit_config()

    # Call edit utility
    vimbox = VimBox()
    vimbox.edit(file_path, create_folder=create_folder)

if __name__ == "__main__":
    main()
