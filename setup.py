import os
# import sys
from setuptools import setup, find_packages
try:  # for pip >=12
    from pip._internal.req import parse_requirements
    from pip._internal import download
except ImportError:  # for pip <= 9.0.3
    from pip.req import parse_requirements
    from pip import download

VERSION='0.4'

# Check if we are on a virtual environment
# https://stackoverflow.com/questions/1871549/determine-if-python-is-running-inside-virtualenv
# if hasattr(sys, 'real_prefix'):

# parse_requirements() returns generator of pip.req.InstallRequirement
# objects
install_reqs = parse_requirements(
    "requirements.txt", session=download.PipSession()
)
# install_requires is a list of requirement
install_requires = [str(ir.req) for ir in install_reqs]

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...


def read(filename):
    return open(os.path.join(os.path.dirname(__file__), filename)).read()


package_data = {
}

setup(
    name='vimbox',
    version=VERSION,
    author='@ramon-astudillo',
    author_email='ramon@astudillo.com',
    description="Manage/edit notes directly in dropbox with vim",
    long_description=read('README.md'),
    # license='MIT',
    py_modules=['vimbox'],
    entry_points={
        'console_scripts': [
            'vimbox = vimbox.__main__:main'
        ]
    },
    packages=find_packages(),
    install_requires=install_requires,
    package_data=package_data,
)
