import os
import sys
#
import dropbox
from dropbox.exceptions import ApiError
from dropbox.files import WriteMode
from requests.exceptions import ConnectionError
#
from vimbox import local


def install_backend(config_file, default_config):

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

        if sys.version_info[0] > 2:
            dropbox_token = input(
                "Press \"generate acess token\" to get one and paste it here: "
            )
        else:
            dropbox_token = raw_input(
                "Press \"generate acess token\" to get one and paste it here: "
            )

        # Validate token by connecting to dropbox
        client = StorageBackEnd(dropbox_token)
        response = client.get_user_account()
        if response['user'] is None:
            print("Could not connect to dropbox %s" % response['status'])
            exit(1)
        else:
            user_acount = response['user']
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
        # TODO: Abstract out this try except in all methods into a wrapper
        out_message = ''
        try:

            # Get user info to validate account
            user = self.dropbox_client.users_get_current_account()
            status = None

        except ConnectionError:

            # Dropbox unrechable
            user = None
            status = 'connection-error'

        except ApiError as exception:

            # API status
            out_message = exception
            user = None
            status = 'api-error'

        return {'status': status, 'content': user, 'alert': out_message}

    def files_upload(self, new_local_content, remote_file_hash):
        assert remote_file_hash[-1] != '/', \
            "Dropbox paths can not finish in /"
        """Overwrites file in the remote"""

        out_message = ''
        try:

            # Upload file to the server
            self.dropbox_client.files_upload(
                new_local_content,
                remote_file_hash,
                mode=WriteMode('overwrite')
            )
            status = None

        except ConnectionError:

            # File non-existing or unreachable
            status = 'connection-error'

        except ApiError as exception:

            # API status
            out_message = exception
            # File non-existing or unreachable
            status = 'api-error'

        return {'status': status, 'content': None, 'alert': out_message}

    def make_directory(self, remote_target):
        assert remote_target[-1] != '/', "Dropbox paths can not finish in /"
        out_message = ''
        try:
            return_value = self.dropbox_client.files_create_folder_v2(
                remote_target
            )
            status = 'online'
        except ConnectionError:
            # This can be missleading
            status = 'connection-error'
        except ApiError as exception:
            import ipdb;ipdb.set_trace(context=30)
            out_message = exception
            status = 'api-error'
        return {'status': status, 'content': None, 'alert': out_message}

    def files_copy(self, remote_source, remote_target):
        assert remote_source[-1] != '/', "Dropbox paths can not finish in /"
        assert remote_target[-1] != '/', "Dropbox paths can not finish in /"
        out_message = ''
        try:
            return_value = self.dropbox_client.files_copy_v2(
                remote_source,
                remote_target
            )
            status = 'online'
        except ConnectionError:
            # This can be missleading
            status = 'connection-error'
        except ApiError as exception:
            out_message = exception
            if type(exception.error._value).__name__ == 'LookupError':
                status = 'online'
            else:
                status = 'api-error'
        return {'status': status, 'content': None, 'alert': out_message}

    def files_delete(self, remote_source):
        assert remote_source[-1] != '/', "Dropbox paths can not finish in /"
        out_message = ''
        try:
            return_value = self.dropbox_client.files_delete_v2(remote_source)
            status = 'online'
        except ConnectionError:
            # This can be missleading
            status = 'connection-error'
        except ApiError as exception:
            if type(exception.error._value).__name__ == 'LookupError':
                status = 'online'
            else:
                out_message = exception
                status = 'api-error'
        return {'status': status, 'content': None, 'alert': out_message}

    def _get_meta_data(self, remote_source):

        try:
            result = self.dropbox_client.files_alpha_get_metadata(
                remote_source
            )
            status = 'online'
        except ConnectionError:
            # This can be missleading
            result = None
            status = 'connection-error'
        except ApiError as exception:
            result = None
            if type(exception.error._value).__name__ == 'LookupError':
                status = 'online'
            else:
                result = exception
                status = 'api-error'

        return result, status

    def file_type(self, remote_source):
        assert remote_source[-1] != '/', "Dropbox paths can not finish in /"
        # Note that with no connection we wont be able to know if the file
        # exists
        alert = ''
        try:
            result = self.dropbox_client.files_alpha_get_metadata(
                remote_source
            )
            if hasattr(result, 'content_hash'):
                file_type = 'file'
            else:
                file_type = 'dir'
            status = 'online'
        except ConnectionError:
            # This can be missleading
            status = 'connection-error'
            file_exists = False
        except ApiError as exception:
            file_type = None
            if type(exception.error._value).__name__ == 'LookupError':
                status = 'online'
            else:
                alert = exception
                status = 'api-error'

        return {'status': status, 'content': file_type, 'alert': alert}

    def file_download(self, remote_file):
        assert remote_file[-1] != '/', "Dropbox paths can not finish in /"
        out_message = ''
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

        except ApiError as exception:

            # File non-existing
            remote_content = None
            if type(exception.error._value).__name__ == 'LookupError':
                status = 'online'
            else:
                out_message = exception
                status = 'api-error'

        return {
            'status': status,
            'content': remote_content,
            'alerts': out_message
        }

    def list_folders(self, remote_folder):
        if remote_folder:
            assert remote_folder[-1] != '/', \
                "Dropbox paths can not finish in /"
        out_message = ''
        try:

            # Get user info to validate account
            result = self.dropbox_client.files_list_folder(remote_folder)
            response = {
                'entries': [x.name for x in result.entries],
                'is_files': [
                    hasattr(x, 'content_hash') for x in result.entries
                 ]
            }
            status = 'online'

        except ConnectionError:

            # Dropbox unrechable
            response = {'entries': None, 'is_files': None }
            status = 'connection-error'

        except ApiError as exception:

            # API status
            if type(exception.error._value).__name__ == 'LookupError':

                if exception.error._value._tag == u'not_folder':
                    # Its a file print meta-data for files
                    out_message = self._get_meta_data(remote_folder)[0]
                    status = 'online'
                    response = {'entries': None, 'is_files': None }

                else:
                    # Nothing found
                    entries = False
                    is_files = None
                    status = 'online'
                    response = {'entries': None, 'is_files': None }

            else:
                out_message = exception
                import ipdb;ipdb.set_trace(context=30)
                response = {'entries': None, 'is_files': None }
                status = 'api-error'

        return {'status': status, 'content': response, 'alerts': out_message}
