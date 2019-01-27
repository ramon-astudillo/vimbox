import requests
import sys
import json
import re
from requests.exceptions import ConnectionError


DROPBOX_PAPER_URL = 'https://paper.dropbox.com/doc/'
IDS_REGEX_STR = '--([A-Za-z0-9_]+)-([A-Za-z0-9_]+)'
DOC_REGEX = re.compile('%s(.*)%s' % (DROPBOX_PAPER_URL, IDS_REGEX_STR))


class FakeApiError(Exception):
    pass


class StorageBackEnd():

    def __init__(self, paper_token):
        self.paper_token = paper_token

    def get_user_account(self):
        """Provide info on users current account"""
        raise NotImplementedError("Not yet implemented")

    def files_upload(self, new_local_content, url):

        # Get meta-data
        doc_metadata = self._get_doc_info_from_url(url)

        # Overwrite with new content

        # Prepare data
        url = 'https://api.dropboxapi.com/2/paper/docs/update'
        headers = {
            'Authorization': 'Bearer %s' % self.paper_token,
            'Content-Type': 'application/octet-stream',
            'Dropbox-API-Arg': json.dumps({
                'doc_id': '%s' % doc_metadata['doc_id'],
                'doc_update_policy': 'overwrite_all',
                'revision': doc_metadata['revision'],
                'import_format': 'markdown',
            })
        }

        # FIXME: This is not clear
        data = new_local_content

        # Protected call
        out_message = ''
        try:

            # Call
            response = requests.post(url, headers=headers, data=data)
            if response.status_code != 200:
                raise FakeApiError(response.text)
            status = None

        except ConnectionError:

            # File non-existing or unreachable
            status = 'connection-error'

        except FakeApiError as exception:

            # API status
            out_message = exception
            # File non-existing or unreachable
            status = 'api-error'

        return {'status': status, 'content': None, 'alert': out_message}

    def make_directory(self, remote_target):
        raise NotImplementedError("Not yet implemented")

    def files_copy(self, remote_source, remote_target):
        raise NotImplementedError("Not yet implemented")

    def files_delete(self, remote_source):
        raise NotImplementedError("Not yet implemented")

    def _get_meta_data(self, remote_source):
        raise NotImplementedError("Not yet implemented")

    def file_type(self, url):

        # Note that with no connection we wont be able to know if the file
        # exists
        alert = ''
        try:

            doc_metadata = self._get_doc_info_from_url(url)
            file_type = 'file'
            status = 'online'

        except ConnectionError:
            # This can be missleading
            file_type = None
            status = 'connection-error'
            file_exists = False

        return {'status': status, 'content': file_type, 'alert': alert}

    def file_download(self, url):

        doc_metadata = self._get_doc_info_from_url(url)

        url = 'https://api.dropboxapi.com/2/paper/docs/download'
        headers = {
            'Authorization': 'Bearer %s' % self.paper_token,
            'Dropbox-API-Arg': json.dumps({
                'doc_id': '%s' % doc_metadata['doc_id'],
                'export_format': 'markdown'
            })
        }

        out_message = ''
        try:

            # Call
            response = requests.post(url, headers=headers)
            # Parse response
            if response.status_code != 200:
                raise FakeApiError(response.text)

            # FIXME: This is not clear
            remote_content = response.text.encode('latin-1')
            status = 'online'

        except ConnectionError:

            # Dropbox unrechable
            remote_content = None
            status = 'connection-error'

        return {
            'status': status,
            'content': remote_content,
            'alerts': out_message
        }

    def list_folders(self, remote_folder):

        raise NotImplementedError("Not yet implemented")

        # Parameters
        url = 'https://api.dropboxapi.com/2/paper/docs/list'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer %s' % self.paper_token
        }
        data = json.dumps({
            'filter_by': 'docs_created',
            'sort_by': 'modified',
            'sort_order': 'descending',
            'limit': 100
        })

        # Call
        response = requests.post(url, headers=headers, data=data)

        # Parse response
        if response.status_code != 200:
            raise Exception(response.text)
        return json.loads(response.text)

    # PRIVATE

    def _get_doc_metadata(self, doc_id):

        url = 'https://api.dropboxapi.com/2/paper/docs/get_metadata'
        headers = {
            'Authorization': 'Bearer %s' % self.paper_token,
            'Content-Type': 'application/json',
        }
        data = json.dumps({'doc_id': '%s' % doc_id})
        response = requests.post(url, headers=headers, data=data)
        if response.status_code != 200:
            raise Exception(response.text)
        return json.loads(response.text)

    def _get_doc_info_from_url(self, url_str):

        _, _, doc_id = DOC_REGEX.match(url_str).groups()
        if DOC_REGEX.match(url_str):
            return self._get_doc_metadata(doc_id)
        else:
            raise Exception("Could not parse URL %s" % url_str)

    def _get_current_account(self):
        response = requests.post(
            'https://api.dropboxapi.com/2/users/get_current_account',
            headers={'Authorization': 'Bearer %s' % self.paper_token}
        )
        # Parse response
        if response.status_code != 200:
            Exception(response.text)
        return json.loads(response.text)
