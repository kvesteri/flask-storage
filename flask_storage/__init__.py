from .amazon import S3BotoStorage, S3BotoStorageFile
from .cloudfiles import CloudFilesStorage, CloudFilesStorageFile
from .filesystem import FileSystemStorage
from .mock import MockStorage, MockStorageFile
from .base import Storage, StorageException

__all__ = (
    CloudFilesStorage,
    CloudFilesStorageFile,
    FileSystemStorage,
    MockStorage,
    MockStorageFile,
    S3BotoStorage,
    S3BotoStorageFile,
    Storage,
    StorageException,
    'STORAGE_DRIVERS',
    'get_default_storage_class',
    'get_filesystem_storage_class',
)


STORAGE_DRIVERS = {
    'amazon': S3BotoStorage,
    'cloudfiles': CloudFilesStorage,
    'filesystem': FileSystemStorage,
    'mock': MockStorage
}


def get_default_storage_class(app):
    return STORAGE_DRIVERS[app.config['DEFAULT_FILE_STORAGE']]


def get_filesystem_storage_class(app):
    if app.config['TESTING']:
        return MockStorage
    else:
        return FileSystemStorage
