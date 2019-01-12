#!/bin/bash
set -o errexit
set -o nounset
set -o pipefail

if [ ! -d tests/ ];then
    echo ""
    echo "bash tests/test_all.sh"
    echo ""
    exit
fi

# Current tests
python tests/test_automerge.py
python tests/test_client.py
python tests/test_dropbox_backend.py
python tests/test_encryption.py fake
python tests/test_encryption.py dropbox
python tests/test_extra.py fake
python tests/test_offline.py
