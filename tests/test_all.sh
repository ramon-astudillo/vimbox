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

for test in $(ls tests/test_*.py);do 
    echo ""
    echo $test
    python $test
    echo ""
done
