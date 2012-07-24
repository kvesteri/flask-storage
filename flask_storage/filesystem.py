import errno
import os
import shutil

from flask import current_app, url_for
from .base import Storage


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
        self.create_folder(directory)

        with open(full_path, 'wb') as destination:
            buffer_size = 16384
            shutil.copyfileobj(content, destination, buffer_size)

        return name

    def delete_folder(self, folder=None):
        if folder is None:
            folder = self.folder_name
        shutil.rmtree(folder)

    def create_folder(self, folder=None):
        if folder is None:
            folder = self.folder_name
        # Create any intermediate directories that do not exist.
        # Note that there is a race between os.path.exists and os.makedirs:
        # if os.makedirs fails with EEXIST, the directory was created
        # concurrently, and we can continue normally. Refs #16082.
        if not os.path.exists(folder):
            try:
                os.makedirs(folder)
            except OSError, e:
                if e.errno != errno.EEXIST:
                    raise
        if not os.path.isdir(folder):
            raise IOError("%s exists and is not a directory." % folder)

    def delete(self, name):
        name = self.path(name)
        # If the file exists, delete it from the filesystem.
        # Note that there is a race between os.path.exists and os.remove:
        # if os.remove fails with ENOENT, the file was removed
        # concurrently, and we can continue normally.
        if os.path.exists(name):
            try:
                os.remove(name)
            except OSError, e:
                if e.errno != errno.ENOENT:
                    raise

    def exists(self, name):
        return os.path.exists(self.path(name))

    def path(self, name):
        return os.path.normpath(os.path.join(self.location, name))

    def url(self, name):
        return url_for('uploads.uploaded_file', filename=name)
