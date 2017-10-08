import sys
from vimbox import VimBox, vim_edit_config, folders


def vimbox_help():
    print("\nvimbox [-f] path/to/file\n")
    exit()


def main(args=None):
    """
    This is renamed as vimbox in setup.py
    """
    if args is None:
        args = sys.argv[1:]

    if '-c' in args:
        vim_edit_config()
        exit()

    elif '-l' in args:
        print("")
        for folder in folders():
            print(folder)
        print("")
        exit()

    # Gather options from command line
    file_path = None
    create_folder = False
    for option in args:
        if option == '-f':
            create_folder = True
        elif file_path is not None:
            vimbox_help()
        else:
            file_path = option

    if file_path is None:
        vimbox_help()

    # Call edit utility
    vimbox = VimBox()
    vimbox.edit(file_path, create_folder=create_folder)

if __name__ == "__main__":
    main()
