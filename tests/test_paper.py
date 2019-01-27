import requests
import sys
import re
import json
from vimbox.local import load_config

OAUTH_TOKEN = load_config()['paper_token']

def get_current_account():
    response = requests.post(
        'https://api.dropboxapi.com/2/users/get_current_account',
        headers={'Authorization': 'Bearer %s' % OAUTH_TOKEN}
    )
    # Parse response
    if response.status_code != 200:
        Exception(response.text)
    return json.loads(response.text)


def get_doc_info_from_url(url_str):

    dropbox_paper_url = 'https://paper.dropbox.com/doc/'
    ids_regex_str = '--([A-Za-z0-9_]+)-([A-Za-z0-9_]+)'
    doc_regex = re.compile('%s(.*)%s' % (dropbox_paper_url, ids_regex_str))
    _, _, doc_id = doc_regex.match(url_str).groups()
    #
    if doc_regex.match(url_str):
        return get_doc_metadata(doc_id)
    else:
        raise Exception("Could not parse URL %s" % url_str)


def list_files(limit=100):

    # Parameters
    url = 'https://api.dropboxapi.com/2/paper/docs/list'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer %s' % OAUTH_TOKEN
    }
    data = json.dumps({
        'filter_by': 'docs_created',
        'sort_by': 'modified',
        'sort_order': 'descending',
        'limit': limit
    })

    # Call
    response = requests.post(url, headers=headers, data=data)

    # Parse response
    if response.status_code != 200:
        raise Exception(response.text)
    return json.loads(response.text)


def download_file(doc_id):

    url = 'https://api.dropboxapi.com/2/paper/docs/download'
    headers = {
        'Authorization': 'Bearer %s' % OAUTH_TOKEN,
        'Dropbox-API-Arg': json.dumps({
            'doc_id': '%s' % doc_id,
            'export_format': 'markdown'
        })
    }

    # Call
    response = requests.post(url, headers=headers)

    # Parse response
    if response.status_code != 200:
        raise Exception(response.text)
    return response.text


def update_file(doc_id, revision, content):

    url = 'https://api.dropboxapi.com/2/paper/docs/update'
    headers = {
        'Authorization': 'Bearer %s' % OAUTH_TOKEN,
        'Content-Type': 'application/octet-stream',
        'Dropbox-API-Arg': json.dumps({
            'doc_id': '%s' % doc_id,
            'doc_update_policy': 'overwrite_all',
            'revision': revision,
            'import_format': 'markdown',
        })
    }
    data = content.encode('utf-8')
    # Call
    response = requests.post(url, headers=headers, data=data)
    if response.status_code != 200:
        raise Exception(response.text)


def get_doc_metadata(doc_id):

    url = 'https://api.dropboxapi.com/2/paper/docs/get_metadata'
    headers = {
        'Authorization': 'Bearer %s' % OAUTH_TOKEN,
        'Content-Type': 'application/json',
    }
    data = json.dumps({'doc_id': '%s' % doc_id})

    response = requests.post(url, headers=headers, data=data)
    if response.status_code != 200:
        raise Exception(response.text)
    return json.loads(response.text)


def create_file(content):

    url = 'https://api.dropboxapi.com/2/paper/docs/create'
    headers = {
        'Authorization': 'Bearer %s' % OAUTH_TOKEN,
        'Content-Type': 'application/octet-stream',
        'Dropbox-API-Arg': json.dumps({
            'import_format': 'markdown',
        })
    }
    data = content.encode('utf-8')
    response = requests.post(url, headers=headers, data=data)
    if response.status_code != 200:
        raise Exception(response.text)
    return json.loads(response.text)


if __name__ == '__main__':

    doc_url = sys.argv[1]
    doc_metadata = get_doc_info_from_url(doc_url)
    document = download_file(doc_metadata['doc_id'])
    update_file(
        doc_metadata['doc_id'],
        doc_metadata['revision'],
        document + u'# Automatic Section\n[ ] Some item\n[ ] Some other item'
    )
