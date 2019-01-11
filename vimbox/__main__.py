import sys
import os
import getpass
# vimbox
from vimbox.remote.primitives import VimboxClient
from vimbox import local, __version__, VimboxClientError, VimboxOfflineError

# Commands and help
COMMAND_HELP = {
    'setup': ('setup', 'set-up dropbox backend'),
    '-f': ('-f /path/to/file [some text]', 'create file'),
    '': ('/path/to/file', 'open created file'),
    '-e': ('-e /path/to/file [some text]', 'create encrypted file'),
    'cache': ('cache', 'show cached folders'),
    'config': ('config', 'open vimbox config in editor'),
    'ls': ('ls /path/to/folder/', 'list files in remote folder, update cache'),
    'rm': ('rm /path/to/folder', 'remove file'),
    'rm -R': ('rm -R /path/to/folder/', 'remove folder'),
    'cp': ('cp /path/to/file /path2/to/[file2]', 'copy file'),
    'mv': ('mv /path/to/file /path2/to/[file2]', 'move file'),
    'cat': ('cat /path/to/file /path2/file', 'concatenate file outputs'),
    'mkdir': ('mkdir /path/to/folder/', 'create folder')
}
COMMAND_ORDER = [
    'setup', '-f', '-e', '', 'cache', 'config', 'ls', 'rm', 'rm -R', 'cp',
    'mv', 'cat', 'mkdir'
]


def assert_valid_path(file_path, path_type=None):
    if file_path.find('//') != -1:
        return "Paths can not have double slashes"
    if path_type == 'file' and file_path[-1] == '/':
        return "File paths can not finish in slash"
    elif path_type == 'dir' and file_path[-1] != '/':
        return "Folder paths must finish in slash"
    return None


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
    if not os.path.isdir("%s/DATA/" % local.ROOT_FOLDER):
        os.mkdir("%s/DATA/" % local.ROOT_FOLDER)
        print("Created %s/DATA/" % local.ROOT_FOLDER)

    # Configure back-end
    # Right now only dropbox
    from vimbox.remote.dropbox_backend import install_backend
    install_backend(local.CONFIG_FILE, local.DEFAULT_CONFIG)

    # Modify bashrc
    local.modify_bashrc(virtualenv)
    print("vimbox %s installed sucessfully\n" % __version__)
    return True


def password_prompt(remote_file, config):

    # Check if file in cache already
    if remote_file in config['path_hashes'].values():
        VimboxClientError(
            '\nCan not re-encrypt a registered file.\n'
        )

    # Prompt for password
    password = getpass.getpass('Input file password: ')
    password2 = getpass.getpass('Repeat file password: ')
    if not password:
        VimboxClientError("Passwords can not be empty!")
    if password != password2:
        VimboxClientError("Passwords do not match!")

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
            return None

    # Sanity checks
    # Check we got a file path
    if remote_file is None:
        return None

    # Quick exit: edit file is a folder
    if remote_file[-1] == '/' and encrypt:
        VimboxClientError('\nOnly files can be encrypted\n')

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


def offline_edit(local_file, initial_text):

    if not os.path.isfile(local_file) and initial_text:
        dirname = os.path.dirname(local_file)
        if not os.path.isdir(dirname):
            os.makedirs(dirname)
        local.write_file(local_file, initial_text)
    else:
        local.edittool(local_file)


def main(args=None, config_path=None, password=None, verbose=1):
    """
    This is refered as vimbox in setup.py
    """

    # Argument handling
    if config_path is None:
        config_path = local.CONFIG_FILE
    if args is None:
        # From command line
        args = sys.argv[1:]
    if len(args) == 0:
        vimbox_help()
        return False
    # Sanity check: back-end is installed
    if (
        args[0] not in ['setup', 'complete'] and
        not os.path.isfile(local.CONFIG_FILE)
    ):
        print("\nMissing config in %s\nRun vimbox setup\n" % local.CONFIG_FILE)
        exit(1)

    #
    # LOCAL COMMANDS (will work offline)
    #

    if args[0] == 'help':

        # help
        if len(args) > 1 and args[1] in COMMAND_ORDER:
            vimbox_help(args[1])
        else:
            vimbox_help()
        return True

    elif args[0] == 'complete':

        # strings to store when calling command -W in .basrc
        for autocomplete_option in local.get_complete_arguments():
            print(autocomplete_option)
        return True

    elif args[0] == 'local':

        if len(args) == 2:
            print(local.get_local_file(args[1]))
            return True
        else:
            vimbox_help()
            return False

    elif args[0] == 'cache':

        # Folders cached in this computer (latter minus commans e.g. ls)
        for cached_file in sorted(local.get_cache()):
            print(cached_file)
        return True

    elif args[0] == 'local':

        if len(args) == 2:
            alert = assert_valid_path(args[1])
            if alert:
                print("%s" % alert)
                return False
            print(local.get_local_file(args[1]))
        else:
            vimbox_help()
            return False

    elif args[0] == 'config':

        # Open config in editor
        local.edit_config()
        return True

    elif args[0] == 'setup':

        # Set-up back-end
        try:
            install()
            return True
        except VimboxOfflineError:
            print("\nCan not install vimbox offline! (keep the token)")
            return False

    #
    # REMOTE COMMANDS (some may have offline functionalities)
    #

    elif args[0] == 'ls':

        # List contents of folder

        # Argument handling
        if len(args) == 1:
            argument = ''
        elif len(args) == 2:
            argument = args[1]
            alert = assert_valid_path(argument)
            if alert:
                print("%s" % alert)
                return False
        else:
            vimbox_help()
            return False

        # Client
        client = VimboxClient(config_path=config_path, verbose=verbose)
        try:
            client.list_folders(argument)
            return True
        except VimboxClientError as exception:
            print("%s" % str(exception))
            return False

    elif args[0] == 'mkdir':

        # Copy file to file or folder
        client = VimboxClient(config_path=config_path, verbose=verbose)
        if len(args) != 2:
            vimbox_help()
            return False
        try:
            alert = assert_valid_path(args[1], path_type='dir')
            if alert:
                print("%s" % alert)
                return False
            client.make_directory(args[1])
            return True
        except VimboxOfflineError:
            print("\nCan not create folders offline")
            return False
        except VimboxClientError as exception:
            print("\n%s" % str(exception))
            return False

    elif args[0] == 'cp':

        # Argument handling
        if len(args) != 3:
            vimbox_help()
            return False

        # Copy file to file or folder
        client = VimboxClient(config_path=config_path, verbose=verbose)
        try:
            alert = assert_valid_path(args[1])
            if alert:
                print("%s" % alert)
                return False
            alert = assert_valid_path(args[2])
            if alert:
                print("%s" % alert)
                return False
            client.copy(args[1], args[2])
            return True
        except VimboxOfflineError:
            print("\nCan not copy files offline")
            return False
        except VimboxClientError as exception:
            print("\n%s" % str(exception))
            return False

    elif args[0] == 'cat':

        # Copy file to file or folder
        client = VimboxClient(config_path=config_path, verbose=verbose)
        for arg in args[1:]:
            try:
                alert = assert_valid_path(arg, path_type='file')
                if alert:
                    print("%s" % alert)
                    return False
                client.cat(arg)
                return True
            except VimboxClientError as exception:
                print("\n%s" % str(exception))
                return False

    elif args[0] == 'rm':

        # Remove file or folder

        # argument processing
        if len(args) == 2:
            arguments = args[1]
            recursive_flag = False
        elif len(args) == 3 and args[1] == '-R':
            arguments = args[2]
            recursive_flag = True
        else:
            vimbox_help()
            return False

        # Call client
        client = VimboxClient(config_path=config_path, verbose=verbose)
        try:
            alert = assert_valid_path(arguments)
            if alert:
                print("%s" % alert)
                return False
            client.remove(arguments, recursive=recursive_flag)
            return True
        except VimboxOfflineError:
            print("\nCan not remove files offline")
            return False
        except VimboxClientError as exception:
            print("%s" % str(exception))
            return False

    elif args[0] == 'mv':

        # Move file to file or folder

        # Argument handling
        if len(args) != 3:
            vimbox_help()
            return False

        # Call client
        client = VimboxClient(config_path=config_path, verbose=verbose)
        try:
            alert = assert_valid_path(args[1])
            if alert:
                print("%s" % alert)
                return False
            alert = assert_valid_path(args[2])
            if alert:
                print("%s" % alert)
                return False
            client.move(args[1], args[2])
            return True
        except VimboxOfflineError:
            print("\nCan not move files offline")
            return False
        except VimboxClientError as exception:
            print("%s" % str(exception))
            return False

    else:

        # Get flags from arguments
        arguments = argument_handling(args)
        if not arguments:
            vimbox_help()
            return False
        remote_file, force_creation, encrypt, initial_text = arguments
        alert = assert_valid_path(remote_file)
        if alert:
            print("%s" % alert)
            return False

        if remote_file[-1] == '/':

            # Alias for ls
            client = VimboxClient(config_path=config_path, verbose=verbose)
            client.list_folders(remote_file)
            return True

        else:

            # Edit

            # Get config
            client = VimboxClient(config_path=config_path, verbose=verbose)

            # Create new encrypted file or register existing one
            # TODO: This should happend inside of the client
            if encrypt and password is None:
                try:
                    password = password_prompt(remote_file, client.config)
                except VimboxClientError as exception:
                    print("%s" % str(exception))
                    return False

            # Call function
            try:
                client.edit(
                    remote_file,
                    force_creation=force_creation,
                    password=password,
                    initial_text=initial_text
                )
                return True

            except VimboxOfflineError:

                # Offline mode
                local_file = local.get_local_file(remote_file)
                if password:
                    print("\nCan not create encrypted files offline")
                    return False
                else:
                    # Extra edit mode offline
                    offline_edit(local_file, initial_text)
                    return True

            except VimboxClientError as exception:
                print("%s" % str(exception))
                return False


if __name__ == "__main__":
    main()
