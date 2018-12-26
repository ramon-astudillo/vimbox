"""
Contains remote primitives indepenedent of back-end used and back-end switch

Handles back-end errors in a unified way
"""
import os
import sys
import re
import shutil
import getpass
#
from vimbox import local
from vimbox import crypto
from vimbox import diogenes


# Bash font styles
red = diogenes.style(font_color='light red')
yellow = diogenes.style(font_color='yellow')
green = diogenes.style(font_color='light green')
blue = diogenes.style(font_color='light blue')

class VimboxClientError(Exception):
    pass

class VimboxOfflineError(Exception):
    pass

def get_path_components(path):
    return tuple(filter(None, path.split('/')))


def automerge(reference_content, modified_content, automerge_rules):

    # Ensure allowed automerge rules
    valid_rules = {
        'append',        # Append an line at the end of the reference
        'prepend',       # Prepend an line at the  beginning of the reference
        'insert',        # Insert one or more line in the reference
        'line-append',   # Append text to a line of the ref
        'line-prepend',  # Prepend text to a line of the ref
        'ignore-edit',   # Admissible line edit
    }
    if isinstance(automerge_rules, dict):
        rules = set(automerge_rules)
    else:
        rules = automerge_rules
    for rule in rules:
        assert rule in valid_rules, "Unknown rule %s" % rule
    if 'ignore-edit' in automerge_rules:
        non_editable = re.compile(automerge_rules['ignore-edit'])

    # Work with separate lines
    reference_lines = reference_content.split('\n')
    modified_lines = modified_content.split('\n')
    num_lines_modified = len(modified_lines)
    num_lines_reference = len(reference_lines)

    # Quick exits
    if (
        'append' in automerge_rules and
        modified_lines[:num_lines_reference] == reference_lines
    ):
        return modified_content, 'append'
    if (
        'prepend' in automerge_rules and
        modified_lines[-num_lines_reference:] == reference_lines
    ):
        return modified_content, 'prepend'

    # Simplified closed edit distance. We only admit insertions and controlled
    # line edits so its linear over
    # max(num_lines_reference, num_lines_modified - num_lines_reference)
    merge_strategy = set()
    modified_cursor = 0
    reference_cursor = 0
    valid_modification = False
    while (
        num_lines_modified - modified_cursor >=
            num_lines_reference - reference_cursor
    ):
        # Get current lines
        modified_line = modified_lines[modified_cursor]
        reference_line = reference_lines[reference_cursor]
        num_char_ref = len(reference_line)

        # Try to align modified with reference, advance over modified otherwise
        if modified_line == reference_line:
            # Matches
            modified_cursor += 1
            reference_cursor += 1
        elif (
            'line-prepend' in automerge_rules and
            modified_line[-num_char_ref:] == reference_line
        ):
            # Matches prepending to this line of modified
            merge_strategy |= set(['line-prepend'])
            modified_cursor += 1
            reference_cursor += 1
        elif 'ignore-edit' in automerge_rules and (
                non_editable.match(reference_line) and
                non_editable.match(modified_line) and
                non_editable.match(reference_line).groups() ==
                    non_editable.match(modified_line).groups()
            ):
            # Matches in the parts specified by the regexp
            merge_strategy |= set(['ignore-edit'])
            modified_cursor += 1
            reference_cursor += 1
        elif (
            'line-append' in automerge_rules and
            modified_line[:num_char_ref] == reference_line
        ):
            # Matches appending to this line of modified
            merge_strategy |= set(['line-append'])
            modified_cursor += 1
            reference_cursor += 1
        elif 'prepend' in automerge_rules and modified_cursor == 0:
            # Line prepended to modified
            merge_strategy |= set(['prepend'])
            modified_cursor += 1
        elif (
            'append' in automerge_rules and
            modified_cursor == num_lines_local - 1
        ):
            # Line appended to modified
            merge_strategy |= set(['append'])
            modified_cursor += 1
        elif 'insert' in automerge_rules:
            # Line inserted in modified
            merge_strategy |= set(['insert'])
            modified_cursor += 1
        else:
            # No valid modification, exit
            merge_strategy |= set([None])
            break

        # If we consumed all the reference it's a valid modification
        if reference_cursor == num_lines_reference:
            valid_modification = True
            # If we did not consume modified, this is also a append
            if modified_cursor < num_lines_modified - 1:
                merge_strategy |= set(['append'])
            break

    if valid_modification:
        merge_strategy = "+".join(merge_strategy)
        merged_content = modified_content
    else:
        merge_strategy = None
        merged_content = None

    return merged_content, merge_strategy


def copy_hash(path_hashes, source_folder, target_folder, verbose):

    # Do not allow to copy encrypted files or folder containing them
    updated_hashes = False
    for key in path_hashes.keys():
        if path_hashes[key][:len(source_folder)] == source_folder:
            if target_folder[-1] == '/':
                new_key = target_folder + \
                    key[len(source_folder):]
                new_path = target_folder + \
                    path_hashes[key][len(source_folder):]
            else:
                new_key = target_folder + '/' + \
                    key[len(source_folder):]
                new_path = target_folder + '/' + \
                    path_hashes[key][len(source_folder):]
            path_hashes.update({new_key: new_path})
            if verbose > 0:
                print("Copied hash %s -> %s" % (path_hashes[key], new_path))
            updated_hashes = True

    return updated_hashes


class VimboxClient():

    def __init__(self, config_path=local.CONFIG_FILE, verbose=1):

        # Load local config if not provided
        self.config_path = config_path
        self.config = local.load_config(config_path)
        self.verbose = verbose

        # Get reference to remote client
        if self.config['backend_name'] == 'dropbox':
            from vimbox.remote.dropbox_backend import (
                install_backend,
                StorageBackEnd
            )
            # Install if necessary
            if self.config.get('DROPBOX_TOKEN', None) is None:
                install_backend(self.config_path, local.DEFAULT_CONFIG)
            self.client = StorageBackEnd(self.config['DROPBOX_TOKEN'])

        elif self.config['backend_name'] in ['fake', 'fake-offline']:
            from vimbox.remote.fake_backend import (
                install_backend,
                StorageBackEnd
            )
            if self.config is None:
                install_backend(self.config_path, local.DEFAULT_CONFIG)
            if self.config['backend_name'] == 'fake-offline':
                online = False
            else:
                online = True
            self.client = StorageBackEnd(online=online)

        else:
            raise Exception(
                "Unknown backend %s" % self.config['backend_name']
            )

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
        self.client.files_upload(new_local_content, remote_file_hash)

    def _tentative_fetch(self, remote_file, password):

        # Initial assumption about encryption
        if password:
            is_encrypted = True
            remote_file_hash = crypto.get_path_hash(remote_file)
            response = self.client.file_download(remote_file_hash)
        else:
            is_encrypted = False
            response = self.client.file_download(remote_file)

        if response['status'] == 'api-error':
            # Unexpected error
            raise VimboxClientError("api-error:\n%s" % response['alerts'])

        elif response['status'] == 'connection-error':
            # Offline
            raise VimboxOfflineError("Connection error")

        elif response['content'] == False:

            # No file found, but need to check for hashed / unhashed name
            # collision
            if password:
                # We asked for an encrypted file, try unencrypted
                response = self.client.file_download(remote_file)
            else:
                # We asked for an unencrypted file try encrypted
                remote_file_hash = crypto.get_path_hash(remote_file)
                response = self.client.file_download(remote_file_hash)

            if response['status'] == 'api-error':
                # Unexpected error
                # This one is weird, since we tried once and it was ok
                raise VimboxClientError("api-error:\n%s" % response['alerts'])

            elif response['status'] == 'connection-error':
                # Suddenly, Offline
                raise VimboxOfflineError("Connection error")

            elif response['content'] == False:
                # File really does not exist
                pass

            elif password:

                # Provided a password but the file exists unencrypted in remote
                VimboxClientError(
                    "Tried to fetch encrypted version of %s but it exists "
                    "unencrypted in remote" % remote_file
                )

            else:

                # Tried to fetch as unecrypted but it is encrypted
                is_encrypted = True

        return response, is_encrypted

    def fetch(self, remote_file, password=None):
        """
        Get local and remote content and coresponding file paths
        """

        # Name of the remote file
        assert remote_file[0] == '/', "Dropbox remote paths start with /"
        assert remote_file[-1] != '/', "Can only fetch files"

        # Fetch file without assumptions about encryption
        response, is_encrypted = self._tentative_fetch(remote_file, password)

        # Decryption
        if response['content'] and is_encrypted:
            if not password:
                password = getpass.getpass('Input file password: ')
            validated_password = crypto.validate_password(password)
            response['content'], sucess = crypto.decript_content(
                remote_content, validated_password
            )
            if not sucess:
                raise VimboxClientError("Decrypting %s filed" % remote_file)

        return response, password

    def merge(self, remote_file, remote_content, automerge_rules,
              amerge_ref_is_local):

        # Fetch local content for this file
        local_file, local_content = self.get_local_content(remote_file)

        # Merge
        if remote_content is None:
            if local_content is None:
                merged_content = None
            else:
                merged_content = local_content

        elif local_content and local_content != remote_content:

            # If automerge selected try one or more strategies
            merge_strategy = None
            if automerge_rules:
                # Select reference. Automerge will try to keep the information
                # in it according to the rules. If it fails manual merge will
                # fire.
                if amerge_ref_is_local:
                    merged_content, merge_strategy = automerge(
                        local_content,
                        remote_content,
                        automerge_rules,
                    )
                else:
                    merged_content, merge_strategy = automerge(
                        remote_content,
                        local_content,
                        automerge_rules,
                    )

            if merge_strategy is None:
                old_local_file = "%s.local" % local_file
                local.write_file(old_local_file, local_content)
                local.write_file(local_file, remote_content)
                local.mergetool(old_local_file, local_file)
                merged_content = local.read_file(local_file)
                # Clean up extra temporary file
                os.remove(old_local_file)
            else:
                local.write_file(local_file, merged_content)
                if self.verbose > 0:
                    print("merged by %s" % merge_strategy)

        else:

            # No local content, or local matches remote
            merged_content = remote_content
            local.local_edit(local_file, merged_content, no_edit=True)

        return {
            'local': local_content,
            'remote': remote_content,
            'merged': merged_content
        }

    def pull(self, remote_file, force_creation, password=None,
             automerge_rules=None, amerge_ref_is_local=False):

        # Fetch remote content for this file. If the is connction error, use
        # offline mode
        response, password = self.fetch(remote_file, password=password)

        # Force use of -f or -e to create new folders
        if (
            response['status'] == 'online' and
            response['content'] == False and
            not force_creation and
            not local_content
        ):
            VimboxClientError('You need to create a file, use -f or -e')

        # Merge
        if response['status'] == 'online':
            content = self.merge(
                remote_file,
                response['content'],
                automerge_rules,
                amerge_ref_is_local
            )
        else:
            raise VimboxClientError("Connection error")

        return content, 'online', password

    def cat(self, remote_file):
        """ Equivalent of bash cat in remote """
        response, password = self.fetch(remote_file)
        if response['status'] == 'online' and self.verbose > 0:
            print(response['content'])

    def list_folders(self, remote_folder):
        """ list folder content in remote """

        # Try first remote
        if remote_folder and remote_folder[-1] == '/':
             response = self.client.list_folders(remote_folder[:-1])
        else:
             response = self.client.list_folders(remote_folder)
        entries = response['content']['entries']
        is_files = response['content']['is_files']
        status = response['status']
        message = response['alerts']

        # Second try to see if there is an ecrypted file
        is_encrypted = False
        if status == 'online' and entries == False:
            remote_folder = crypto.get_path_hash(remote_folder)
            # entries, is_files, status, message = \
            response = self.client.list_folders(remote_folder)
            entries = response['content']['entries']
            is_files = response['content']['is_files']
            status = response['status']
            message = response['alerts']
            is_encrypted = status == 'online'

        if status == 'api-error':
            raise VimboxClientError("api-error")

        elif status == 'online' and entries == False:
            # Folder/File non existing
            raise VimboxClientError(
                "%s does not exist in remote" % remote_folder
            )

        elif status == 'online' and entries is None:
            # This was a file
            return True

        elif status == 'online':

            # Differentiate file and folders
            display_folders = []
            for entry, is_file in zip(entries, is_files):
                # Add slash to files on root
                if remote_folder == '':
                    entry = '/' + entry
                if is_file:
                    # File
                    display_folders.append(entry)
                else:
                    # Folder
                    display_folders.append("%s/" % entry)
            display_folders = sorted(display_folders)

            # Update to match folder
            if remote_folder:

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
                local.write_config(self.config_path, self.config)

            # Replace encrypted files
            entry_types = []
            new_display_folders = []
            for entry in display_folders:
                key = "%s%s" % (remote_folder, entry)
                if key in self.config['path_hashes'].keys():
                    entry_types.append('encrypted')
                    new_display_folders.append(
                        os.path.basename(self.config['path_hashes'][key])
                    )
                elif entry[-1] == '/':
                    entry_types.append('folder')
                    new_display_folders.append(entry)
                else:
                    entry_types.append(None)
                    new_display_folders.append(entry)
            display_folders = new_display_folders

            # Display entries sorted and with colors
            new_display_folders = []
            indices = sorted(
                range(len(display_folders)),
                key=display_folders.__getitem__
            )
            for file_folder, entry_type in zip(display_folders, entry_types):
                if entry_type == 'encrypted':
                    file_folder = red(file_folder)
                elif entry_type == 'folder':
                    file_folder = blue(file_folder)
                new_display_folders.append(file_folder)
            display_string = "".join(
                ["%s\n" % new_display_folders[index] for index in indices]
            )

            # Add file to cache
            if remote_folder not in self.config['cache']:
                self.config['cache'].append(remote_folder)
                local.write_config(self.config_path, self.config)

        else:

            # If it fails resort to local cache
            display_folders = local.list_local(remote_folder, self.config)
            if self.verbose > 0:
                print("\n%s content for %s " % (red("offline"), remote_folder))
            display_string = "".join(
                ["%s\n" % folder for folder in sorted(display_folders)]
            )

        # Print
        if self.verbose > 0:
            print("\n%s\n" % display_string.rstrip())

    def make_directory(self, remote_target):
        if remote_target[-1] != '/':
            raise VimboxClientError("Folder paths must end in / ")
        file_type, is_encripted, status = self.file_type(remote_target[:-1])
        if status != 'online':
            raise VimboxClientError(
                "%s can not create files/folders" % red("offline")
            )

        if file_type is None:
            response = self.client.make_directory(remote_target[:-1])
            if response['status'] == 'online':
                self.register_file(remote_target, False)
        elif file_type == 'dir':
            raise VimboxClientError("%s already exists" % remote_target)
        elif is_encripted:
            raise VimboxClientError(
                "%s already exists as an encrypted file" % remote_target
            )
        else:
            raise VimboxClientError(
                "%s already exists as a file" % remote_target
            )

        return {
            'status': status,
            'content': None,
            'alert': None
        }

    def copy(self, remote_source, remote_target):
        """
        This should support:

        cp /path/to/file /path/to/another/file
        cp /path/to/file /path/to/folder/
        cp /path/to/folder/ /path/to/another_folder/
        """

        # Map `cp /path/to/file /path2/` to `cp /path/to/file /path/file`
        if remote_target[-1] == '/':
            file_type, is_encripted, status = self.file_type(
                remote_target[:-1]
            )
            if file_type == 'dir':
                if remote_source[-1] == '/':
                    addendum = os.path.basename(remote_source[:-1])
                    remote_target = remote_target + addendum + '/'
                else:
                    addendum = os.path.basename(remote_source)
                    remote_target = remote_target + addendum
        else:
            file_type, is_encripted, status = self.file_type(remote_target)
            if file_type:
                raise VimboxClientError(
                    'Target file %s exists' % remote_target
                )

        # Move paths in hash
        updated_hashes = copy_hash(
            self.config['path_hashes'],
            remote_source,
            remote_target,
            self.verbose
        )
        if updated_hashes:
            local.write_config(self.config_path, self.config)

        # For folder we need to remove the ending back-slash
        if remote_source[-1] == '/':
            remote_source = remote_source[:-1]
        if remote_target[-1] == '/':
            remote_target = remote_target[:-1]

        response = self.client.files_copy(remote_source, remote_target)
        if response['status'] != 'connection-error':
            self.register_file(remote_target, False)
            if self.verbose > 0:
                print(
                    "%-12s %s %s" % (
                        yellow("copied"),
                        remote_source,
                        remote_target
                    )
                )
        elif self.verbose > 0:
            print("%-12s did not copy!" % red("offline"))

    def is_removable(self, remote_file):
        """Check if file/folder is removable"""
        # Disallow deleting of encrypted files that have unknown name. Also
        # consider the unfrequent file is registered but user uses hash name
        if remote_file[-1] == '/':
            remote_file = remote_file[:-1]
        # Disallow deleting of folders.
        file_type, is_encrypted, status = self.file_type(remote_file)
        if status != 'online':
            is_rem = False
            reason = 'We are offline'
        elif file_type == 'dir':
            is_rem = True
            reason = None
            pass
        elif (
            remote_file not in self.config['path_hashes'].values() and
            is_encrypted
        ):
            is_rem = False
            reason = "Can not delete uncached encrypted files"
        else:
            is_rem = True
            reason = None

        return is_rem, reason

    def remove(self, remote_file, recursive=False, password=None):

        if remote_file == '/':
            raise VimboxClientError(
                "\nRemoving root is disallowed, just in case you have fat"
                " fingers\n"
            )

        # Extra check for deletable files/folders
        if remote_file[-1] == '/':
            remote_file = remote_file[:-1]
        is_rem, reason = self.is_removable(remote_file)
        if not is_rem:
            raise VimboxClientError("\nCan not remove. %s\n" % reason)

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
            response = self.client.files_delete(remote_file[:-1])
            # update cache
            # local.update_cache()
        else:
            response = self.client.files_delete(remote_file)

        if response['status'] == 'api-error':

            # Remove local copy
            local_file = self.get_local_file(remote_file)
            if os.path.isfile(local_file):
                os.remove(local_file)
            elif os.path.isdir(local_file):
                shutil.rmtree(local_file)
            self.unregister_file(remote_file)
            if self.verbose > 0:
                print("%s did not exist in remote!" % original_name)

        elif response['status'] != 'connection-error':
            if self.verbose > 0:
                print("%-12s %s" % (yellow("removed"), original_name))

            # Remove local copy
            local_file = self.get_local_file(remote_file)
            if os.path.isfile(local_file):
                os.remove(local_file)
            elif os.path.isdir(local_file):
                shutil.rmtree(local_file)
            self.unregister_file(remote_file)
        elif self.verbose > 0:
            print(
                "%-12s did not remove!  %s" % (red("offline"), original_name)
            )

    def move(self, remote_source, remote_target):
        """Copy and remove"""
        is_rem, reason = self.is_removable(remote_source)
        if not is_rem:
            raise VimboxClientError(
                "Can not move (remove) due to %s" % reason
            )
        self.copy(remote_source, remote_target)
        self.remove(remote_source)

    def edit(self, remote_file, remove_local=None, force_creation=False,
             register_folder=True, password=None, initial_text=None,
             automerge_rules=None, amerge_ref_is_local=False):
        """
        Edit or create existing file

        Edits will happen on a local copy that will be uploded when finished.

        remove_local        After sucesful push remove local content
        force_creation      Mandatory for new file on remote
        register_folder     Store file path in local cache
        password            Optional encryption/decription on client side
        automerge_rules     Allowed way to automerge
        amerge_ref_is_local If valid automerge use local as reference (default
                            is remote)
        """

        if initial_text:

            def manual_edit(local_file, content):
                """Write empty file with given text"""
                if content['remote']:
                    if content['remote'] == content['merged']:
                        return content['merged']
                    elif content['remote'] != content['merged']:
                        raise Exception(
                            "File exists in remote and differs in content"
                        )
                else:
                    return local.local_edit(
                        local_file,
                        initial_text,
                        no_edit=True
                    )

        else:

            def manual_edit(local_file, content):
                """Prompt user for edit"""
                return local.local_edit(local_file, content['merged'])

        self.sync(
            remote_file,
            remove_local=remove_local,
            force_creation=force_creation,
            register_folder=register_folder,
            password=password,
            automerge_rules=automerge_rules,
            amerge_ref_is_local=amerge_ref_is_local,
            edits=manual_edit
        )

    def sync(self, remote_file, remove_local=None, force_creation=False,
             register_folder=True, password=None, automerge_rules=None,
             amerge_ref_is_local=False, edits=None):
        """
        Syncronize remote and local content with optional edit

        Edits will happen on a local copy that will be uploded when finished.

        remove_local        After sucesful push remove local content
        force_creation      Mandatory for new file on remote
        register_folder     Store file path in local cache
        password            Optional encryption/decription on client side
        automerge_rules     Allowed way to automerge
        amerge_ref_is_local If valid automerge use local as reference (default
                            is remote)
        """

        # Sanity checks
        if remote_file[-1] == '/':
            raise VimboxClientError("Can not edit folders")
        elif (
            remote_file in self.config['path_hashes'].values() and
            force_creation
        ):
            raise VimboxClientError(
                '\n%s exists in remote and is encrypted.\n' % remote_file
            )
        if remove_local is None:
            remove_local = self.config['remove_local']

        # Fetch remote content, merge if neccesary with local.mergetool
        # local_content, remote_content, merged_content
        content, fetch_status, password = self.pull(
            remote_file,
            force_creation,
            password=password,
            automerge_rules=automerge_rules,
            amerge_ref_is_local=amerge_ref_is_local
        )

        if (
            force_creation and
            content['local'] and
            content['remote'] is None and
            self.verbose > 0
        ):
            print("\nRecovered local version from %s\n" % remote_file)

        # Apply edit if needed
        if edits:
            local_file = self.get_local_file(remote_file)
            content['edited'] = edits(local_file, content)
        else:
            # Why this?
            content['edited'] = content['merged']

        # update local and remote

        # Abort if file being created but no changes
        if (
            content['edited'] is None and
            content['remote'] is not None and
            fetch_status != 'connection-error'
        ):
            # For debug purposes
            VimboxClientError(
                "\nInvalid state: edited local_file non existing but remote"
                " does\n"
            )

        # Pull again if recovered offline status
        if fetch_status == 'connection-error':
            content2, fetch_status, password = self.pull(
                remote_file,
                force_creation,
                password=password,
                automerge_rules=automerge_rules,
                amerge_ref_is_local=amerge_ref_is_local
            )
            if fetch_status != 'connection-error':
                content = content2
                content['edited'] = content['remote']

        # Update remote
        if content['edited'] != content['remote']:

            # Try to push into remote
            if fetch_status != 'connection-error':
                error = self._push(
                    content['edited'],
                    remote_file,
                    password=password
                )
            else:
                error = 'connection-error'

            # Inform the user
            if error is None:
                # We pushed sucessfully
                if self.verbose > 0:
                    print("%-12s %s" % (yellow("pushed"), remote_file))
            elif error == 'connection-error':
                # Offline
                if self.verbose > 0:
                    print("%-12s %s" % (red("offline"), remote_file))
            elif error == 'api-error':
                # This is not a normal state. Probably bug on our side or API
                # change/bug on the backend.
                if self.verbose > 0:
                    print("%-12s %s" % (red("api-error"), remote_file))
                    print("API error (something bad happened)")
            else:
                # This is most certainly a bug on our side
                raise Exception("Unknown _push error %s" % error)

            # Update local after updating remote

            # Register file in cache
            if register_folder and error != 'api-error':
                self.register_file(remote_file, password is not None)

            # Remove local copy if solicited, otherwise update it with new
            # content
            local_file = self.get_local_file(remote_file)
            if remove_local and os.path.isfile(local_file):
                if (
                    content['merged'] != content['remote'] and
                    error is not None
                ):
                    # If we could not update the remote but we are forced to
                    # remove the file we must prompt user first
                    _ = input(
                        "We are offline but I have to remove local files."
                        " Will open the file once more for you to save "
                        "stuff, then it will be nuked. (press any key "
                        "when ready)"
                    )
                    local.local_edit(local_file, content['merged'])
                # Remove local file if solicited
                os.remove(local_file)
                if self.verbose > 0:
                    print("%-12s %s" % (red("cleaned"), local_file))

            elif content['local'] != content['merged']:
                # If local content was changed we need to update
                local.local_edit(local_file, content['merged'], no_edit=True)

        elif content['merged'] != content['local'] and not remove_local:
            # We overwrote local with remote
            local_file = self.get_local_file(remote_file)
            local.local_edit(local_file, content['merged'], no_edit=True)
            if self.verbose > 0:
                print("%-12s %s" % (yellow("pulled"), remote_file))
            if register_folder:
                self.register_file(remote_file, password is not None)

        else:
            # No changes needed on either side
            if self.verbose > 0:
                print("%-12s %s" % (green("in-sync"), remote_file))
            if remove_local and os.path.isfile(local_file):
                os.remove(local_file)
                if self.verbose > 0:
                    print("%-12s %s" % (red("cleaned"), local_file))
            if register_folder:
                self.register_file(remote_file, password is not None)

        return content['local'] == content['remote']

    def file_type(self, remote_file):
        response = self.client.file_type(remote_file)
        if response['content'] == None and response['status'] == 'online':
            # I file not found, try hashed name version
            remote_file = crypto.get_path_hash(remote_file)
            response = self.client.file_type(remote_file)
            is_encrypted = False
            if response['content']:
                is_encrypted = True
        elif response['content'] == 'file':
            is_encrypted = False
        else:
            is_encrypted = None
        return response['content'], is_encrypted, response['status']

    # LOCAL METHODS

    def get_local_file(self, remote_file):
        return local.get_local_file(remote_file, self.config)

    def register_file(self, remote_file, is_encrypted):
        return local.register_file(remote_file, self.config, is_encrypted)

    def unregister_file(self, remote_file):
        return local.unregister_file(remote_file, self.config)

    def get_local_content(self, remote_file):
        return local.get_local_content(remote_file, self.config)
