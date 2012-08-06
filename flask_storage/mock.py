import os
from .base import Storage, FileNotFoundError


class MockStorage(Storage):
    """
    A mock storage class for testing
    """
    _files = {}

    def __init__(self, folder_name=None):
        self.folder_name = folder_name

    def _save(self, name, content):
        self._files[name] = str(content)
        return name

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


class MockStorageFile(object):
    def __init__(self, storage, name):
        self._name = name
        try:
            self._file = storage._files[name]
        except KeyError:
            raise FileNotFoundError()
        self._pos = 0

    @property
    def size(self):
        return len(self._file)

    def read(self, size=None):
        if self._pos == self.size:
            return ''
        size = min(size, self.size - self._pos)
        data = self._file[self._pos:self.size]
        self._pos += len(data)
        return data

    def seek(self, offset, whence=os.SEEK_SET):
        if whence == os.SEEK_SET:
            self._pos = offset
        elif whence == os.SEEK_CUR:
            self._pos += offset
        elif whence == os.SEEK_END:
            self._pos = self.size + offset
        else:
            raise IOError(22, 'Invalid argument')

    def tell(self):
        return self._pos
