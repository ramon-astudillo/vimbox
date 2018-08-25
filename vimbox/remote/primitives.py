"""
Contains remote primitives indepenedent of back-end used and back-end switch

Handles back-end errors in a unified way
"""
import os
import sys
import shutil
import getpass
#
from requests.exceptions import ConnectionError
#
from vimbox import local
from vimbox import crypto
from vimbox import diogenes


# Bash font styles
red = diogenes.style(font_color='light red')
yellow = diogenes.style(font_color='yellow')
green = diogenes.style(font_color='light green')


def get_path_components(path):
    return tuple(filter(None, path.split('/')))


class VimboxClient():

    def __init__(self, backend_name):

        # Load local config if not provided
        self.config = local.load_config()

        # Get reference to remote client
        if backend_name == 'dropbox':
            from vimbox.remote.dropbox_api import (
                install_backend,
                StorageBackEnd
            )
            # Install if not prsent
            if self.config.get('DROPBOX_TOKEN', None) is None:
                install_backend(local.CONFIG_FILE, local.DEFAULT_CONFIG)
            self.client = StorageBackEnd(self.config['DROPBOX_TOKEN'])

        elif backend_name == 'fake':

            # TODO: Fake backend for unit testing
            raise NotImplementedError()

        else:
            raise Exception("Unknown backend %s" % backend_name)

    # REMOTE METHODS

    def _push(self, new_local_content, remote_file, password=None):
        """
        Push updates to remote

        NOTE: This overwrites remote content. It can lead to loss of data.
        """

        # If encrypted get encrypted remote-name
        if password is not None:
            # Validate pasword
            validated_password = crypto.validate_password(password)
            # Hash filename
            remote_file_hash = crypto.get_path_hash(remote_file)
            # Encript content
            new_local_content = crypto.encrypt_content(
                new_local_content,
                validated_password
            )
        else:
            remote_file_hash = remote_file
            if sys.version_info[0] > 2:
                # Encoding for Python3
                new_local_content = str.encode(new_local_content)
        # Overwrite remote
        self.client.files_upload(
            new_local_content,
            remote_file_hash,
        )

    def fetch(self, remote_file, password=None):
        """
        Get local and remote content and coresponding file paths
        """

        # Name of the remote file
        assert remote_file[0] == '/', "Dropbox remote paths start with /"
        assert remote_file[-1] != '/', "Can only fetch files"

        remote_content, status = self.client.file_download(
            remote_file,
        )

        if status == 'online' and remote_content is None:

            # File does not exist, try encrypted name
            remote_file_hash = crypto.get_path_hash(remote_file)
            remote_content, status = self.client.file_download(
                remote_file_hash,
            )

            if remote_content:
                # Fond encrypted content, decrypt
                if not password:
                    password = getpass.getpass('Input file password: ')
                validated_password = crypto.validate_password(password)
                remote_content, sucess = crypto.decript_content(
                    remote_content, validated_password
                )

                # FIXME: This needs to be taken into consideration
                # If encryption is used we need to register the file in the
                # cache
                # if not register_folder:
                #    print('\nFile encryption only with register_folder = True\n')
                #    EXIT()

                if not sucess:
                    status = 'decription-failed'
                    password = None

        return remote_content, status, password

    def pull(self, remote_file, force_creation, password=None):

        # Fetch local content for this file
        local_file, local_content = self.get_local_content(remote_file)

        # Fetch remote content for this file
        # Note: Will try encrypted path if clean path fails
        remote_content, fetch_status, password = self.fetch(
            remote_file,
            password=password
        )

        # Quick exit on decription failure
        if fetch_status == 'decription-failed':
            print('\nDecription failed check password and vimbox version\n')
            exit(0)

        # Force use of -f to create new folders
        if (
            fetch_status == 'online' and
            remote_content is None and
            not force_creation and
            not local_content
        ):
            print('\nYou need to create a file, use -f or -e\n')
            exit(0)

        # Merge
        if remote_content is None:

            # No file in remote (we could be creating one or syncing after
            # offline)
            merged_content = None

        elif local_content is not None and local_content != remote_content:

            # Content conflict, call local.mergetool
            old_local_file = "%s.local" % local_file
            local.write_file(old_local_file, local_content)
            local.write_file(local_file, remote_content)
            local.mergetool(old_local_file, local_file)
            merged_content = local.read_file(local_file)
            # Clean up extra temporary file
            os.remove(old_local_file)

        else:

            # No local content, or local matches remote
            merged_content = remote_content

        content = {
            'local': local_content,
            'remote': remote_content,
            'merged': merged_content
        }

        return content, fetch_status, password

    def cat(self, remote_file):
        """ Equivalent of bash cat in remote """
        remote_content, status, _ = self.fetch(remote_file)
        if status == 'online':
            print(remote_content)

    def list_folders(self, remote_folder):
        """ list folder content in remote """

        if remote_folder == '/':
            remote_folder = ''

        # NotImplementedYet: Listing of files
        if remote_folder and remote_folder[-1] != '/':
            print("\nOnly /folders/ can be listed right now\n")
            exit(1)

        # Try first remote
        result, error = self.client.list_folders(remote_folder)
        if result:

            # Differentiate file and folders
            display_folders = []
            for x in result.entries:
                if hasattr(x, 'content_hash'):
                    # File
                    display_folders.append(x.name)
                else:
                    # Folder
                    display_folders.append("%s/" % x.name)
            display_folders = sorted(display_folders)

            # Update to match folder
            if remote_folder and remote_folder[-1] == '/':

                # Remove folder paths no more in remote
                for path in self.config['cache']:
                    if path[:len(remote_folder)] == remote_folder:
                        cache_folder = \
                            path[len(remote_folder):].split('/')[0] + '/'
                        if (
                            cache_folder not in display_folders and
                            cache_folder != ''
                        ):
                            self.config['cache'].remove(path)

                # Add missing folders
                if remote_folder not in self.config['cache']:
                    self.config['cache'].append(remote_folder)
                for folder in display_folders:
                    if folder[-1] == '/':
                        new_path = "%s%s" % (remote_folder, folder)
                        if new_path not in self.config['cache']:
                            self.config['cache'].append(new_path)

                # Write cache
                self.config['cache'] = sorted(self.config['cache'])
                local.write_config(local.CONFIG_FILE, self.config)

            # Display encrypted files in red
            new_display_folders = []
            for file_folder in display_folders:
                key = "%s%s" % (remote_folder, file_folder)
                path_hashes = self.config['path_hashes']
                if key in path_hashes:
                    file_folder = red(os.path.basename(path_hashes[key]))
                new_display_folders.append(file_folder)
            display_string = "".join(
                ["%s\n" % folder for folder in sorted(new_display_folders)]
            )

            # Add file to cache
            if remote_folder not in self.config['cache']:
                self.config['cache'].append(remote_folder)
                local.write_config(local.CONFIG_FILE, self.config)

        elif error == 'api-error':

            display_string = "Folder does not exist in remote!"

        else:

            # If it fails resort to local cache
            display_folders = local.list_local(remote_folder, self.config)
            print("\n%s content for %s " % (red("offline"), remote_folder))
            display_string = "".join(
                ["%s\n" % folder for folder in sorted(display_folders)]
            )

        # Print
        print("\n%s\n" % display_string.rstrip())

    def copy(self, remote_source, remote_target):

        # Map `cp /path/to/file /path2/` to `cp /path/to/file /path/file`
        if remote_target[-1] == '/':
            basename = os.path.basename(remote_source)
            remote_target = "%s%s" % (remote_target, basename)
            if remote_source == remote_target:
                print("source and target are the same")
                exit(1)

        # Do not allow to copy encrypted files or folder containing them
        hashed_paths = set([
            get_path_components(path)
            for path in self.config['path_hashes'].values()
        ])
        hashed_remote_source = get_path_components(remote_source)
        hashed_remote_target = get_path_components(remote_target)
        # Add also partial paths
        hashed_paths |= set([
            path[:len(hashed_remote_source)] for path in hashed_paths
        ])
        hashed_paths |= set([
            path[:len(hashed_remote_target)] for path in hashed_paths
        ])
        if (
            hashed_remote_source in hashed_paths or
            hashed_remote_target in hashed_paths or
            crypto.is_encrypted_path(remote_source) or
            crypto.is_encrypted_path(remote_target)
        ):
            print("\ncopy/move operations can not include encrypted files\n")
            exit(1)

        # For folder we need to remove the ending back-slash
        if remote_source[-1] == '/':
            remote_source = remote_source[:-1]
        if remote_target[-1] == '/':
            remote_target = remote_target[:-1]
        sucess = self.client.files_copy(remote_source, remote_target)
        if sucess:
            print(
                "%12s %s %s" % (
                    yellow("copied"),
                    remote_source,
                    remote_target
                )
            )

    def remove(self, remote_file, force=False, password=None):

        # Disallow deleting of encrypted files that have unknown name. Also
        # consider the unfrequent file is registered but user uses hash name
        if (
            remote_file not in self.config['path_hashes'] and
            crypto.is_encrypted_path(remote_file)
        ):
                print("Can not delete uncached encrypted files")
                exit(1)

        # Disallow deleting of folders.
        # TODO: Handle hashing in encrypter files here
        if not force and not self.is_file(remote_file)[0]:
            result, error = self.client.list_folders(remote_file)
            if error:
                print("Could not find %s" % remote_file)
                exit(1)

            if result.entries != []:
                print("Can only delete empty folders")
                exit(1)

        # Hash name if necessary
        if remote_file in self.config['path_hashes'].values():
            original_name = remote_file
            remote_file = crypto.get_path_hash(remote_file)
        else:
            original_name = remote_file

        # TODO: This should go to the client specific part and have exception
        # handling
        if remote_file[-1] == '/':
            # Remove backslash
            # TODO: This is input sanity check should go in the client
            # dependent part
            sucess = self.client.files_delete(remote_file[:-1])
        else:
            sucess = self.client.files_delete(remote_file)

        if sucess:
            print("%12s %s" % (yellow("removed"), original_name))

            # Remove local copy
            local_file = self.get_local_file(remote_file)
            if os.path.isfile(local_file):
                os.remove(local_file)
            elif os.path.isdir(local_file):
                #shutil.rmtree(local_file)
                os.rmdir(local_file)
            # Unregister if it is a folder
            if remote_file[-1] == '/' and remote_file in self.config['cache']:
                self.config['cache'].remove(remote_file)
                local.write_config(local.CONFIG_FILE, self.config)

            # If encrypted remove from path_hashes
            if remote_file in self.config['path_hashes']:
                del self.config['path_hashes'][remote_file]
                local.write_config(local.CONFIG_FILE, self.config)

    def edit(self, remote_file, remove_local=None, diff_mode=False,
             force_creation=False, register_folder=True, password=None):
        """
        Edit or create existing file

        Edits will happen on a local copy that will be uploded when finished.

        remove_local     After sucesful push remove local content
        diff_mode        Only pull and push, no editing
        force_creation   Mandatory for new file on remote
        register_folder  Store file path in local cache
        password         Optional encryption/decription on client side
        """

        # Checks
        if remote_file[-1] == '/':
            print("Can not edit folders")
            exit()

        # Initialize backend
        if remove_local is None:
            remove_local = self.config['remove_local']

        # Trying to create a registered file
        if (
            remote_file in self.config['path_hashes'].values() and
            force_creation
        ):
            print('\nCan not re-encrypt a registered file.\n')
            exit()

        # Fetch remote content, merge if neccesary with local.mergetool
        # local_content, remote_content, merged_content
        content, fetch_status, password = self.pull(
            remote_file,
            force_creation,
            password=password
        )

        if force_creation and content['remote']:
            print("\nFile exists, can not be created\n")
            exit(1)

        # Needed variable names
        local_file = self.get_local_file(remote_file)

        # Call editor on merged code if solicited
        # TODO: Programatic edit operations here
        if diff_mode:

            if remove_local:
                content['edited'] = content['merged']
            else:
                # Dummy no edit, but still makes local copy
                content['edited'] = local.local_edit(
                    local_file,
                    content['merged'],
                    no_edit=True
                )
        else:
            # Edit with edit tool and retieve content
            content['edited'] = local.local_edit(
                local_file,
                content['merged']
            )

        # Abort if file being created but no changes
        if content['edited'] is None and fetch_status != 'connection-error':
            # For debug purposes
            assert force_creation, \
                "Invalid state: edited local_file non existing but remote does"
            # File creation aborted
            exit()

        # Pull again if recovered offline status
        if fetch_status == 'connection-error':
            content, fetch_status, password = self.pull(
                remote_file,
                force_creation,
            )

        # TODO: Need hardening against offline model and edit colision
        if content['edited'] != content['remote']:

            # Update remote if there are changes

            # Push changes to dropbox. If the pull just failed because
            # connection was not there, do not push
            if fetch_status != 'connection-error':
                error = self._push(
                    content['edited'],
                    remote_file,
                    password=password
                )
            else:
                error = 'connection-error'

            # Remove local file
            if error is None:

                # Everything went fine
                print("%12s %s" % (yellow("pushed"), remote_file))

                # Register file in cache
                if register_folder:
                    # TODO: Right now we only register the folder
                    # NOTE: We try this anyway because of independen hash
                    # resgistration
                    self.register_file(remote_file, password is not None)

                # Remove local copy if solicited
                if remove_local and os.path.isfile(local_file):
                    # Remove local file if solicited
                    os.remove(local_file)
                    print("%12s %s" % (red("cleaned"), local_file))

            elif error == 'connection-error':

                # We are offline. This is a plausible state. Just keep local
                # copy TODO: Course of action if remove_local = True
                print("%12s %s" % (red("offline"), remote_file))
                print("keeping local copy")

                # We do still register the file in cache
                if register_folder:
                    # TODO: Right now we only register the folder
                    # NOTE: We try this anyaway because of independen hash
                    # resgistration
                    self.register_file(remote_file, password is not None)

            elif error == 'api-error':

                # This is not a normal state. Probably bug on our side or API
                # change/bug on the backend.
                print("%12s %s" % (red("api-error"), remote_file))
                print("API error (something bad happened)")
                print("keeping local copy")

                # Note that we not register file.
                # TODO: How to operate with existing, unregistered files. We
                # only register folder so this is a bit difficult.

            else:

                # This can only be a bug on our side
                raise Exception("Unknown _push error %s" % error)

        elif content['local'] != content['remote']:
            # We overwrote local with remote
            print("%12s %s" % (yellow("pulled"), remote_file))

            # Register file in cache
            if register_folder:
                # TODO: Right now we only register the folder
                # NOTE: We try this anyaway because of independen hash
                # resgistration
                self.register_file(remote_file, password is not None)

        else:
            # No changes needed on either side
            print("%12s %s" % (green("in-sync"), remote_file))

            # Register file in cache
            if register_folder:
                # TODO: Right now we only register the folder
                # NOTE: We try this anyaway because of independen hash
                # resgistration
                self.register_file(remote_file, password is not None)

    def is_file(self, remote_file):

        is_file, status = self.client.is_file(remote_file)

        if status == 'api-error':
            # I file not found, try hashed version
            remote_file = crypto.get_path_hash(remote_file)
            is_file, status = self.client.is_file(remote_file)
            is_encripted = is_file
        else:
            is_encripted = False

        return is_file, is_encripted, status


    # LOCAL METHODS

    def get_local_file(self, remote_file):
        return local.get_local_file(remote_file, self.config)

    def register_file(self, remote_file, is_encripted):
        return local.register_file(remote_file, self.config, is_encripted)

    def get_local_content(self, remote_file):
        return local.get_local_content(remote_file, self.config)
