import os
import codecs
from vimbox import local


def install_backend(self, config_file, config):
    vimbox_folder = os.path.dirname(config_file)
    if not os.path.isdir(vimbox_folder):
        os.makedirs(vimbox_folder)
    local.write_config(config_file, config)
    print("Created config in %s" % config_file)


class StorageBackEnd():

    def __init__(self, online=True):
        self.fake_remote_folder = os.path.realpath(
            "/%s/../../tests/.fake_remote/" % os.path.dirname(__file__)
        )
        # Create storage folder if it does not exit
        if not os.path.isdir(self.fake_remote_folder):
            os.makedirs(self.fake_remote_folder)
        self.online = online   

    def get_user_account(self):
        """Provide info on users current account"""
        if self.online:
            user = 'fake user'
            # errors = [None, 'connection-error', 'api-error']
            error = None
        else:
            user = None
            # errors = [None, 'connection-error', 'api-error']
            error = 'connection-error'
        return user, error 

    def _remote_write(self, remote_file, remote_content):
        # Store content
        fake_remote_file = "%s/%s" % (
            self.fake_remote_folder, remote_file
        )
        #with codecs.open(fake_remote_file, 'w', 'utf-8') as fid:
        with open(fake_remote_file, 'w') as fid:
            fid.write(remote_content)

    def _remote_read(self, remote_file):
        # Store content
        fake_remote_file = "%s/%s" % (
            self.fake_remote_folder, remote_file
        )
        #with codecs.open(fake_remote_file, 'r', 'utf-8') as fid:
        with open(fake_remote_file, 'r') as fid:
            remote_content = fid.read()
        return remote_content

    def files_upload(self, new_local_content, remote_file_hash):
        """Overwrites file in the remote"""
        # errors = [None, 'connection-error', 'api-error']
        if self.online:
            # Make folder if it does not exist
            dirname = "%s/%s" % (
                self.fake_remote_folder,
                os.path.dirname(remote_file_hash)
            )
            if not os.path.isdir(dirname):
                os.makedirs(dirname)
            self._remote_write(remote_file_hash, new_local_content)
            error = None
        else:
            error = 'connection-error'
        return error

    def files_copy(self, remote_source, remote_target):
        if self.online:
            remote_content = self._remote_read(remote_source)
            self._remote_write(remote_target, remote_content)
            error = None
        else:
            error = 'connection-error'

    def files_delete(self, remote_source):
        if self.online:
            fake_remote_source = "%s/%s" % (
                self.fake_remote_folder, remote_source
            )
            if os.path.isfile(fake_remote_source):
                os.remove(fake_remote_source)
            elif os.path.isdir(fake_remote_source):
                os.rmdir(fake_remote_source)
            error = True
        else:
            error = 'connection-error'
        return error

    def is_file(self, remote_source):
        """ Returns true if remote_file is a file """
        if self.online:
            # stata = ['online', 'connection-error', 'api-error']
            is_file = os.path.isfile("%s/%s" % (
                self.fake_remote_folder,
                remote_source
            ))
            status = 'online'
        else:
            status = 'connection-error'
        return is_file, status

    def file_download(self, remote_source):
        # stata = ['online', 'connection-error']
        if self.online:
            fake_remote_source = "%s/%s" % (
                self.fake_remote_folder, remote_source
            )
            if os.path.isfile(fake_remote_source):
                remote_content = self._remote_read(remote_source)
                status = 'online'
            else:
                remote_content = None
                status = 'online'
        else:
            remote_content = None
            status = 'connection-error'
        return remote_content, status

    def list_folders(self, remote_folder):
        # errors = [None, 'connection-error', 'api-error']
        if self.online:
            return os.listdir(remote_folder), None
        else:
            return 'connection-error', None
