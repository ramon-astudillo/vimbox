import sys
import os
import getpass
# vimbox
from vimbox.remote import primitives
from vimbox import local
from vimbox import __version__

# Commands and help
COMMAND_HELP = {
    'setup': ('setup', 'set-up dropbox backend'),
    '-f': ('-f /path/to/file', 'create file'),
    '': ('/path/to/file', 'open created file'),
    '-e': ('-e /path/to/file', 'create encrypted file'),
    'cache': ('cache', 'show cached folders'),
    'config': ('config', 'open vimbox config in editor'),
    'ls': ('ls /path/to/folder/', 'list files in remote folder, update cache'),
    'rm': ('rm /path/to/folder', 'remove file'),
    'rm -R': ('rm -R /path/to/folder/', 'remove folder'),
    'cp': ('cp /path/to/file /path2/to/[file2]', 'copy file'),
    'mv': ('mv /path/to/file /path2/to/[file2]', 'move file'),
    'cat': ('cat /path/to/file /path2/file', 'concatenate file outputs')
}
COMMAND_ORDER = [
    'setup', '-f', '-e', '', 'cache', 'config', 'ls', 'rm', 'rm -R', 'cp',
    'mv', 'cat'
]


def install():

    # Check if we are in virtual environment
    virtualenv = False
    if hasattr(sys, 'real_prefix'):
        virtualenv = True
        print("\nVirtual environment detected: %s" % sys.prefix)

    # Create config folder
    if not os.path.isdir(local.ROOT_FOLDER):
        os.mkdir(local.ROOT_FOLDER)
        print("Created %s" % local.ROOT_FOLDER)

    # Configure back-end
    # Right now only dropbox
    from vimbox.remote.dropbox_backend import install_backend
    install_backend(local.CONFIG_FILE, local.DEFAULT_CONFIG)

    # Modify bashrc
    local.modify_bashrc(virtualenv)
    print("vimbox %s installed sucessfully\n" % __version__)


def password_prompt(remote_file, config):

    # Check if file in cache already
    if remote_file in config['path_hashes'].values():
        print('\nCan not re-encrypt a registered file.\n')
        exit()

    # Prompt for password
    password = getpass.getpass('Input file password: ')
    password2 = getpass.getpass('Repeat file password: ')
    if not password:
        print("Passwords can not be empty!")
        exit()
    if password != password2:
        print("Passwords do not match!")
        exit()

    return password


def argument_handling(args):

    # Edit / ls alias
    remote_file = None
    force_creation = False
    encrypt = False
    initial_text = None
    for option in args:
        if option == '-f':
            # Create new file
            force_creation = True
        elif option == '-e':
            # Create new encrypted file
            force_creation = True
            encrypt = True
        elif option[0] == '/':
            assert not remote_file, \
                "Only one file path can be edited at a time"
            # Dropbox path
            remote_file = option
        elif force_creation and remote_file:
            # If there is an extra argument not matching the previous and we
            # are in creation mode, admit this is as initial text
            initial_text = option
        else:
            vimbox_help()

    # Sanity checks
    # Check we got a file path
    if remote_file is None:
        vimbox_help()

    # Quick exit: edit file is a folder
    if remote_file[-1] == '/' and encrypt:
        print('\nOnly files can be encrypted\n')
        exit()

    return remote_file, force_creation, encrypt, initial_text


def vimbox_help(command=None):

    print("\nvimbox %s" % __version__)

    if command is None:
        print("")
        for command in COMMAND_ORDER:
            print("vimbox %-35s %s" % COMMAND_HELP[command])
        print("")
    else:
        print("\nvimbox %-35s %s\n" % COMMAND_HELP[command])
    exit()


def main(args=None, config_path=None, password=None):
    """
    This is refered as vimbox in setup.py
    """

    if config_path is None:
        config_path = local.CONFIG_FILE

    if args is None:
        # From command line
        args = sys.argv[1:]

    if len(args) == 0:
        vimbox_help()
        exit(1)

    # Sanity check: back-end is installed
    if args[0] not in ['setup', 'complete']:
        local.local_install_check()

    if args[0] == 'help':

        # help
        if len(args) > 1 and args[1] in COMMAND_ORDER:
            vimbox_help(args[1])
        else:
            vimbox_help()

    elif args[0] == 'setup':

        # Set-up back-end
        install()

    elif args[0] == 'complete':

        # strings to store when calling command -W in .basrc
        for autocomplete_option in local.get_complete_arguments():
            print(autocomplete_option)

    elif args[0] == 'cache':

        # Folders cached in this computer (latter minus commans e.g. ls)
        for cached_file in sorted(local.get_cache()):
            print(cached_file)
        # update cache
        # local.update_cache()

    elif args[0] == 'config':

        # Open config in editor
        local.edit_config()

    elif args[0] == 'ls':

        # List contents of folder
        client = primitives.VimboxClient(config_path=config_path)
        if len(args) == 1:
            client.list_folders('')
        elif len(args) == 2:
            client.list_folders(args[1])
        else:
            vimbox_help()

    elif args[0] == 'mkdir':

        # Copy file to file or folder
        client = primitives.VimboxClient(config_path=config_path)
        if len(args) == 2:
            client.make_directory(args[1])
        else:
            vimbox_help()

    elif args[0] == 'cp':

        # Copy file to file or folder
        client = primitives.VimboxClient(config_path=config_path)
        if len(args) == 3:
            client.copy(args[1], args[2])
        else:
            vimbox_help()

    elif args[0] == 'cat':

        # Copy file to file or folder
        client = primitives.VimboxClient(config_path=config_path)
        for arg in args[1:]:
            client.cat(arg)

    elif args[0] == 'rm':

        # Remove file or folder
        client = primitives.VimboxClient(config_path=config_path)
        if len(args) == 2:
            client.remove(args[1], recursive=False)
        elif len(args) == 3 and args[1] == '-R':
            client.remove(args[2], recursive=True)
        else:
            vimbox_help()

    elif args[0] == 'mv':

        # Move file to file or folder
        client = primitives.VimboxClient(config_path=config_path)
        if len(args) == 3:
            client.move(args[1], args[2])
        else:
            vimbox_help()

    else:

        # Get flags from arguments
        remote_file, force_creation, encrypt, initial_text = \
            argument_handling(args)

        if remote_file[-1] == '/':

            # Alias for ls
            client = primitives.VimboxClient(config_path=config_path)
            client.list_folders(remote_file)

        else:

            # Edit

            # Get config
            client = primitives.VimboxClient(config_path=config_path)

            # Create new encrypted file or register existing one
            if encrypt and password is None:
                password = password_prompt(remote_file, client.config)

            # Call function
            client.edit(
                remote_file,
                force_creation=force_creation,
                password=password,
                initial_text=initial_text
            )

if __name__ == "__main__":
    main()
