import os
import sys
import shutil 
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
            "%s/../../tests/.fake_remote/" % os.path.dirname(__file__)
        )
        # Create storage folder if it does not exit
        if not os.path.isdir(self.fake_remote_folder):
            os.makedirs(self.fake_remote_folder)
        self.online = online

    def get_user_account(self):
        """Provide info on users current account"""
        if self.online:
            user = 'fake user'
            status = None
        else:
            user = None
            status = 'connection-status'
        return {'status': status, 'content': user, 'alerts': None}

    def _remote_write(self, remote_file, remote_content):
        # Store content
        fake_remote_file = "%s/%s" % (
            self.fake_remote_folder, remote_file
        )
        with open(fake_remote_file, 'wb') as fid:
            fid.write(remote_content)

    def _remote_read(self, remote_file):
        # Store content
        fake_remote_file = "%s/%s" % (
            self.fake_remote_folder, remote_file
        )
        with open(fake_remote_file, 'rb') as fid:
            remote_content = fid.read()
        return remote_content

    def _remote_makedir(self, remote_folder):
        # Store content
        fake_remote_file = "%s/%s" % (self.fake_remote_folder, remote_folder)
        os.makedirs(fake_remote_file)

    def _remote_copy_dirs(self, remote_source, remote_target):
        fake_rem_source = "%s/%s" % (self.fake_remote_folder, remote_source)
        fake_rem_target = "%s/%s" % (self.fake_remote_folder, remote_target)
        shutil.copytree(fake_rem_source, fake_rem_target)

    def files_upload(self, new_local_content, remote_file_hash):
        """Overwrites file in the remote"""
        if self.online:
            # Make folder if it does not exist
            dirname = "%s/%s" % (
                self.fake_remote_folder,
                os.path.dirname(remote_file_hash)
            )
            if not os.path.isdir(dirname):
                os.makedirs(dirname)
            self._remote_write(remote_file_hash, new_local_content)
            status = None
        else:
            status = 'connection-status'
        return {'status': status, 'content': None, 'alerts': None}

    def make_directory(self, remote_target):
        if self.online:
            self._remote_makedir(remote_target)
            status = 'online' 
        else:
            status = 'connection-status'
        return {'status': status, 'content': None, 'alerts': None}

    def files_copy(self, remote_source, remote_target):
        if self.online:
            if os.path.isdir(
                "%s/%s" % (self.fake_remote_folder, remote_source)
            ):
                self._remote_copy_dirs(remote_source, remote_target)
            else:
                remote_content = self._remote_read(remote_source)
                self._remote_write(remote_target, remote_content)
            status = None
        else:
            status = 'connection-status'
        return {'status': status, 'content': None, 'alerts': None}

    def files_delete(self, remote_source):
        if self.online:
            fake_remote_source = "%s/%s" % (
                self.fake_remote_folder, remote_source
            )
            something_exists = False
            if os.path.isfile(fake_remote_source):
                os.remove(fake_remote_source)
                something_exists = True
            elif os.path.isdir(fake_remote_source):
                shutil.rmtree(fake_remote_source)
                something_exists = True
            if something_exists:
                status = 'online'
            else:
                # Unexisting file returns api-status
                status = 'api-status'
        else:
            status = 'connection-status'
        return {'status': status, 'content': None, 'alerts': None}

    def file_type(self, remote_source):
        """ Returns true if remote_file is a file """
        if self.online:
            fake_remote_file = "%s/%s" % (
                self.fake_remote_folder,
                remote_source
            )
            if os.path.isfile(fake_remote_file):
                file_type = 'file' 
            elif os.path.isdir(fake_remote_file):
                file_type = 'dir' 
            else:
                file_type = None
            status = 'online'
        else:
            file_type = None 
            status = 'connection-error'
        return {'status': status, 'content': file_type, 'alerts': None}

    def file_download(self, remote_source):
        if self.online:
            fake_remote_source = "%s/%s" % (
                self.fake_remote_folder, remote_source
            )
            status = 'online'
            if os.path.isfile(fake_remote_source):
                remote_content = self._remote_read(remote_source)
            else:
                remote_content = None
        else:
            remote_content = None
            status = 'connection-error'
        return {'status': status, 'content': remote_content, 'alerts': None}

    def list_folders(self, remote_folder):
        fake_remote_source = "%s/%s" % (
            self.fake_remote_folder, remote_folder
        )
        alerts = ''
        if self.online:
            try:
                entries = os.listdir(fake_remote_source)
                is_files = [
                    os.path.isfile("%s/%s" % (fake_remote_source, entry)) 
                    for entry in entries
                ] 
                status = 'online'
            except OSError:
                if os.path.isfile(fake_remote_source):
                    # It is a file
                    status = 'online'
                    alerts = fake_remote_source
                    entries = None 
                    is_files = None

                else:
                    # Does not exist 
                    status = 'online'
                    entries = False
                    is_files = None
        else:
            status = 'connection-error'
            entries = False
            is_files = None

        response = {'entries': entries, 'is_files': is_files}
        return {'status': status, 'content': response, 'alerts': alerts}
