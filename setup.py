import os
# import sys
from setuptools import setup, find_packages
try:  # for pip >=12
    from pip._internal.req import parse_requirements
    from pip._internal import download
except ImportError:  # for pip <= 9.0.3
    from pip.req import parse_requirements
    from pip import download

VERSION = '0.5.2'

# parse_requirements() returns generator of pip.req.InstallRequirement
# objects
install_reqs = parse_requirements(
    "requirements.txt", session=download.PipSession()
)
# install_requires is a list of requirement
install_requires = [str(ir.req) for ir in install_reqs]


def read(filename):
    return open(os.path.join(os.path.dirname(__file__), filename)).read()


package_data = {}

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
