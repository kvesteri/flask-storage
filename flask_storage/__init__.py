from .amazon import S3BotoStorage, S3BotoStorageFile
from .cloudfiles import CloudFilesStorage, CloudFilesStorageFile
from .filesystem import FileSystemStorage
from .mock import MockStorage, MockStorageFile

__all__ = (
    CloudFilesStorage,
    CloudFilesStorageFile,
    FileSystemStorage,
    MockStorage,
    MockStorageFile,
    S3BotoStorage,
    S3BotoStorageFile,
)


def get_default_storage_class(app):
    return {
        'amazon': S3BotoStorage,
        'cloudfiles': CloudFilesStorage,
        'filesystem': FileSystemStorage,
        'mock': MockStorage
    }[app.config['DEFAULT_FILE_STORAGE']]
