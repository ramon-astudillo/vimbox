import os
import sys
#
import dropbox
from dropbox.exceptions import ApiError
from dropbox.files import WriteMode
from requests.exceptions import ConnectionError
#
from vimbox import local


def install_backend(self, config_file, default_config):

    if os.path.isfile(config_file):
        config = local.read_config(config_file)
        if 'DROPBOX_TOKEN' in config:
            print("Found valid config in %s" % config_file)

    else:

        # Prompt user for a token
        print(
            "\nI need you to create a dropbox app and give me an acess token."
            " Go here \n\nhttps://www.dropbox.com/developers/apps/\n\n"
            "1) Create App, select Dropbox API\n"
            "2) Select either App folder or Full Dropbox\n"
            "3) Name is irrelevant but vimbox may help you remember\n"
        )
        dropbox_token = input(
            "Press \"generate acess token\" to get one and paste it here: "
        )
        dropbox_client = dropbox.Dropbox(dropbox_token)

        # Validate token by connecting to dropbox
        user_acount, error = get_user_account(dropbox_client)
        if user_acount is None:
            print("Could not connect to dropbox %s" % error)
            exit(1)
        else:

            print("Connected to dropbox account %s (%s)" % (
                user_acount.name.display_name,
                user_acount.email)
            )
            # Store
            config = default_config
            config['DROPBOX_TOKEN'] = dropbox_token
            local.write_config(config_file, config)
            print("Created config in %s" % config_file)


class StorageBackEnd():

    def __init__(self, dropbox_token):
        self.dropbox_client = dropbox.Dropbox(dropbox_token)

    def get_user_account(self):
        """Provide info on users current account"""
        try:

            # Get user info to validate account
            user = self.dropbox_client.users_get_current_account()
            error = None

        except ConnectionError:

            # Dropbox unrechable
            user = None
            error = 'connection-error'

        except ApiError as exception:

            # API error
            print(exception)
            user = None
            error = 'api-error'

        return user, error

    def files_upload(self, new_local_content, remote_file_hash):
        """Overwrites file in the remote"""

        try:

            # Upload file to the server
            self.dropbox_client.files_upload(
                new_local_content,
                remote_file_hash,
                mode=WriteMode('overwrite')
            )
            error = None

        except ConnectionError:

            # File non-existing or unreachable
            error = 'connection-error'

        except ApiError as exception:

            # API error
            print(exception)
            # File non-existing or unreachable
            error = 'api-error'

        return error

    def files_copy(self, remote_source, remote_target):
        return self.dropbox_client.files_copy_v2(remote_source, remote_target)

    def files_delete(self, remote_source):
        return self.dropbox_client.files_delete_v2(remote_source)

    def is_file(self, remote_file):
        """ Returns true if remote_file is a file """

        # Note that with no connection we wont be able to know if the file exists
        try:
            result = self.dropbox_client.files_alpha_get_metadata(remote_file)
            file_exists = True
            status = 'online'
        except ConnectionError:
            # This can be missleading
            status = 'connection-error'
            file_exists = False
        except ApiError as exception:
            status = 'api-error'
            file_exists = False

        return file_exists and hasattr(result, 'content_hash'), status

    def file_download(self, remote_file):

        try:

            # Look for remote file, store content
            metadata, response = \
                self.dropbox_client.files_download(remote_file)
            remote_content = response.content
            status = 'online'

            if sys.version_info[0] > 2:
                # Python3
                remote_content = remote_content.decode("utf-8")

        except ConnectionError:

            # Dropbox unrechable
            remote_content = None
            status = 'connection-error'

        except ApiError:

            # File non-existing
            remote_content = None
            status = 'online'

        return remote_content, status

    def list_folders(self, remote_folder):

        try:

            # Get user info to validate account
            result = self.dropbox_client.files_list_folder(remote_folder)
            error = None

        except ConnectionError:

            # Dropbox unrechable
            result = None
            error = 'connection-error'

        except ApiError:

            # API error
            result = None
            error = 'api-error'

        return result, error
