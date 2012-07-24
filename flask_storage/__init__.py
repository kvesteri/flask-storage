from .amazon import S3BotoStorage
from .cloudfiles import CloudFilesStorage
from .filesystem import FileSystemStorage
from .mock import MockStorage

__all__ = (
    CloudFilesStorage,
    FileSystemStorage,
    MockStorage,
    S3BotoStorage,
)


def get_default_storage_class(app):
    return {
        'amazon': S3BotoStorage,
        'cloudfiles': CloudFilesStorage,
        'filesystem': FileSystemStorage,
        'mock': MockStorage
    }[app.config['DEFAULT_FILE_STORAGE']]
