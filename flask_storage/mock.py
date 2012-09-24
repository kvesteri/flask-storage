from datetime import datetime
from .base import Storage, StorageFile, FileNotFoundError


class MockStorage(Storage):
    """
    A mock storage class for testing
    """
    _files = {}

    def __init__(self, folder_name=None):
        self.folder_name = folder_name

    def _save(self, name, content):
        if isinstance(content, basestring):
            self._files[name] = content
        else:
            content.seek(0)
            self._files[name] = content.read()
        return self.open(name)

    def _open(self, name, mode):
        return MockStorageFile(self, name)

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
        return '/uploads/' + name

    def empty(self):
        self._files.clear()

    @property
    def file_class(self):
        return MockStorageFile


class MockStorageFile(StorageFile):
    def __init__(self, storage, name=None):
        self._name = name
        self._storage = storage
        if self._name:
            self.file
        self._pos = 0
        self.last_modified = datetime.now()

    @property
    def name(self):
        return self._name

    @property
    def file(self):
        try:
            return self._storage._files[self._name]
        except KeyError:
            raise FileNotFoundError()

    @property
    def size(self):
        return len(self.file)

    def read(self, size=None):
        if self._pos == self.size:
            return ''
        size = min(size, self.size - self._pos)
        data = self.file[self._pos:self.size]
        self._pos += len(data)
        return data
