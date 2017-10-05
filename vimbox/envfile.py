"""
Simple tool to read from and environment file
"""
import re
import os

ROOT_FOLDER = os.path.dirname(os.path.realpath(__file__))
ENV_PATH = '%s/.env' % ROOT_FOLDER


def load(file_path=ENV_PATH):
    assert os.path.exists(file_path), "Expected .env file in %s" % ROOT_FOLDER
    environment = {}
    with open(file_path) as fid:
        for line in fid.readlines():
            if line.strip() and not re.match(' *#', line):
                key, value = line.rstrip().split('=')
                environment[key.strip()] = value.strip()
    return environment
