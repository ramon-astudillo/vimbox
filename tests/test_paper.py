import requests
import sys
import re
import json
from vimbox.local import load_config


if __name__ == '__main__':

    doc_url = sys.argv[1]

    from vimbox.remote.paper_backend import StorageBackEnd
    client = StorageBackEnd(load_config()['paper_token'])
    reponse = client.file_download(doc_url)
    reponse['content'] += '# New Section\n[ ] New item\n[ ] Some other item'
    import ipdb; ipdb.set_trace(context=30)
    client.files_upload(reponse['content'], doc_url)
