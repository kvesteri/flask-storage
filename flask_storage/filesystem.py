from __future__ import with_statement
import errno
import os
import shutil
import StringIO

from flask import current_app, url_for
from .base import Storage, StorageFile, StorageException, reraise as _reraise


def reraise(exception):
    if exception.errno == errno.EEXIST:
        exception.status = 409
    elif exception.errno == errno.ENOENT:
        exception.status = 404
    exception.message = exception.strerror
    _reraise(exception)


class FileSystemStorage(Storage):
    """
    Standard filesystem storage
    """

    def __init__(self, folder_name=None, file_view=None):
        if folder_name is None:
            folder_name = current_app.config.get(
                'UPLOADS_FOLDER',
                os.path.dirname(__file__)
            )
        if file_view is None:
            file_view = current_app.config.get(
                'FILE_SYSTEM_STORAGE_FILE_VIEW',
                'uploads.uploaded_file'
            )
        self._folder_name = folder_name
        self._file_view = file_view
        self._absolute_path = os.path.abspath(folder_name)

    @property
    def folder_name(self):
        return self._folder_name

    def list_folders(self):
        if not self._absolute_path:
            raise StorageException('No folder given in class constructor.')
        return filter(
            lambda a: os.path.isdir(os.path.join(self._absolute_path, a)),
            os.listdir(self._absolute_path)
        )

    def list_files(self):
        if not self._absolute_path:
            raise StorageException('No folder given in class constructor.')
        return filter(
            lambda a: not os.path.isdir(os.path.join(self._absolute_path, a)),
            os.listdir(self._absolute_path)
        )

    def _save(self, name, content):
        full_path = self.path(name)
        directory = os.path.dirname(full_path)
        try:
            self.create_folder(directory)
        except StorageException, e:
            if e.status_code != 409:
                raise e

        with open(full_path, 'wb') as destination:
            buffer_size = 16384
            # we should allow strings to be passed as content since the other
            # drivers support this too
            if isinstance(content, basestring):
                io = StringIO.StringIO()
                io.write(content)
                content = io

            content.seek(0)
            try:
                shutil.copyfileobj(content, destination, buffer_size)
            except OSError, e:
                reraise(e)
        return self.file_class(self, name)

    def open(self, name, mode='rb'):
        try:
            file_ = self.file_class(self, name)
            file_.file
            return file_
        except IOError, e:
            reraise(e)

    def delete_folder(self, name):
        path = self.path(name)
        try:
            return shutil.rmtree(path)
        except OSError, e:
            reraise(e)

    def create_folder(self, path):
        try:
            return os.makedirs(path)
        except OSError, e:
            reraise(e)

    def delete(self, name):
        name = self.path(name)
        try:
            return os.remove(name)
        except OSError, e:
            reraise(e)

    def exists(self, name):
        return os.path.exists(self.path(name))

    def path(self, name):
        return os.path.normpath(os.path.join(self._absolute_path, name))

    def url(self, name):
        return url_for(self._file_view, filename=name)

    @property
    def file_class(self):
        return FileSystemStorageFile


class FileSystemStorageFile(StorageFile):
    _file = None

    def __init__(self, storage, name=None, prefix=''):
        self._storage = storage
        if name is not None:
            self.name = name
        self.prefix = prefix

    @property
    def file(self):
        if not self._file:
            self._file = open(self.path, 'rb')
        return self._file

    @property
    def path(self):
        return self._storage.path(self.name)

    @property
    def last_modified(self):
        return os.path.getmtime(self.path)

    @property
    def size(self):
        return os.path.getsize(self.path)

    @property
    def url(self):
        return self._storage.url(self.name)

    def tell(self):
        return self.file.tell()

    def read(self, size=-1):
        return self.file.read(size)

    def seek(self, offset, whence=os.SEEK_SET):
        self.file.seek(offset, whence)
