import sys
from vimbox import edit


def main(args=None):
    """
    This is renamed as vimbox in setup.py
    """
    if args is None:
        args = sys.argv[1:]
    if len(args) != 1:
        print("\nvimbox file\n")
        exit()
    edit(args[0])

if __name__ == "__main__":
    main()
