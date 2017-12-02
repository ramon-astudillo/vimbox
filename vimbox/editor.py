import os
from subprocess import call
from vimbox.io import read_file, write_file


def mergetool(old_local_file, local_file):
    # Show content conflict with vimdiff
    print(" ".join(['vimdimf', '%s %s' % (old_local_file, local_file)]))
    call(['vimdiff', old_local_file, local_file])


def edittool(local_file):
    # call your editor
    print(" ".join(['vim', '%s' % local_file]))
    call(['vim', '%s' % local_file])


def local_edit(local_file, local_content):
    if local_content is not None:
        # local_content is None if we start from scratch
        write_file(local_file, local_content)
    edittool(local_file)
    if os.path.isfile(local_file):
        edited_local_content = read_file(local_file)
    else:
        # edited content is None if we start from scratch but do nothing on vim
        edited_local_content = None
    return edited_local_content
