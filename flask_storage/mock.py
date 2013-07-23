import os
from datetime import datetime
from .base import Storage, StorageFile, FileNotFoundError


class MockStorage(Storage):
    """
    A mock storage class for testing
    """
    _files = {}

    def __init__(self, folder_name=''):
        self.folder_name = folder_name

    def _save(self, name, content):
        if isinstance(content, basestring):
            self._files[name] = content
        else:
            content.seek(0)
            self._files[name] = content.read()
        return self.open(name)

    def _open(self, name, mode):
        return self.file_class(self, name)

    def path(self, name):
        """
        Returns a local filesystem path where the file can be retrieved using
        Python's built-in open() function. Storage systems that can't be
        accessed using open() should *not* implement this method.
        """

    def delete(self, name):
        """
        Deletes the specified file from the storage system.
        """
        try:
            del self._files[name]
        except KeyError:
            raise FileNotFoundError()

    def exists(self, name):
        """
        Returns True if a file referened by the given name already exists in
        the storage system, or False if the name is available for a new file.
        """
        return name in self._files

    def url(self, name):
        """
        Returns an absolute URL where the file's contents can be accessed
        directly by a Web browser.
        """
        return os.path.join(self.folder_name, name)

    def empty(self):
        self._files.clear()

    @property
    def file_class(self):
        return MockStorageFile


class MockStorageFile(StorageFile):
    def __init__(self, storage, name=None, prefix=''):
        self._storage = storage
        if name is not None:
            self.name = name

        self.prefix = prefix

        if self.name:
            self.file
        self._pos = 0
        self.last_modified = datetime.now()

    def rename(self, name):
        self._name = name

    @property
    def file(self):
        try:
            return self._storage._files[self.name]
        except KeyError:
            raise FileNotFoundError()

    @property
    def size(self):
        return len(self.file)

    def read(self, size=-1):
        if size < 0:
            size = self.size

        start = self._pos
        end = min(self.size, self._pos + size)
        self._pos = end
        return self.file[start:end]
