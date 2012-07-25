import errno
import os
import shutil
import StringIO

from flask import current_app, url_for
from .base import Storage, StorageException, reraise as _reraise


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

    def __init__(self, folder_name=None):
        if folder_name is None:
            folder_name = current_app.config.get(
                'UPLOADS_FOLDER',
                os.path.dirname(__file__)
            )
        self.folder_name = os.path.abspath(folder_name)

    @property
    def location(self):
        return self.folder_name

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

            try:
                shutil.copyfileobj(content, destination, buffer_size)
            except OSError, e:
                reraise(e)
        return name

    def open(self, name, mode='rb'):
        try:
            open(name, mode)
        except IOError, e:
            reraise(e)

    def delete_folder(self, name):
        path = self.path(name)
        try:
            shutil.rmtree(path)
        except OSError, e:
            reraise(e)

    def create_folder(self, name):
        path = self.path(name)
        try:
            os.makedirs(path)
        except OSError, e:
            reraise(e)

    def delete(self, name):
        name = self.path(name)
        try:
            os.remove(name)
        except OSError, e:
            reraise(e)

    def exists(self, name):
        return os.path.exists(self.path(name))

    def path(self, name):
        return os.path.normpath(os.path.join(self.location, name))

    def url(self, name):
        return url_for('uploads.uploaded_file', filename=name)
