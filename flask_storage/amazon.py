from functools import wraps
import mimetypes

from boto.s3.connection import S3Connection, SubdomainCallingFormat
from boto.exception import S3ResponseError, S3CreateError
from boto.s3.key import Key

from flask import current_app

from .base import (
    FileNotFoundError,
    Storage,
    StorageException,
    StorageFile,
    reraise
)


class S3BotoStorage(Storage):
    def __init__(
            self,
            folder_name=None,
            access_key=None,
            secret_key=None,
            bucket_acl=None,
            acl=None,
            headers=None,
            gzip=None,
            gzip_content_types=None,
            querystring_auth=None,
            querystring_expire=None,
            reduced_redundancy=None,
            custom_domain=None,
            secure_urls=None,
            location=None,
            file_name_charset=None,
            preload_metadata=None,
            calling_format=None,
            file_overwrite=None,
            auto_create_bucket=None):

        self.access_key = access_key or \
            current_app.config.get('AWS_ACCESS_KEY_ID', None)
        self.secret_key = secret_key or \
            current_app.config.get('AWS_SECRET_ACCESS_KEY', None)
        self.calling_format = calling_format or \
            current_app.config.get(
                'AWS_S3_CALLING_FORMAT',
                SubdomainCallingFormat()
            )
        self.auto_create_bucket = auto_create_bucket or \
            current_app.config.get('AWS_AUTO_CREATE_BUCKET', False)
        self.bucket_name = folder_name or \
            current_app.config.get('AWS_STORAGE_BUCKET_NAME', None)
        self.acl = acl or \
            current_app.config.get('AWS_DEFAULT_ACL', 'public-read')
        self.bucket_acl = bucket_acl or \
            current_app.config.get('AWS_BUCKET_ACL', self.acl)
        self.file_overwrite = file_overwrite or \
            current_app.config.get('AWS_S3_FILE_OVERWRITE', False)
        self.headers = headers or \
            current_app.config.get('AWS_HEADERS', {})
        self.preload_metadata = preload_metadata or \
            current_app.config.get('AWS_PRELOAD_METADATA', False)
        self.gzip = gzip or \
            current_app.config.get('AWS_IS_GZIPPED', False)
        self.gzip_content_types = gzip_content_types or \
            current_app.config.get(
                'GZIP_CONTENT_TYPES', (
                    'text/css',
                    'application/javascript',
                    'application/x-javascript',
                )
            )
        self.querystring_auth = querystring_auth or \
            current_app.config.get('AWS_QUERYSTRING_AUTH', True)
        self.querystring_expire = querystring_expire or \
            current_app.config.get('AWS_QUERYSTRING_EXPIRE', 3600)
        self.reduced_redundancy = reduced_redundancy or \
            current_app.config.get('AWS_REDUCED_REDUNDANCY', False)
        self.custom_domain = custom_domain or \
            current_app.config.get('AWS_S3_CUSTOM_DOMAIN', None)
        self.secure_urls = secure_urls or \
            current_app.config.get('AWS_S3_SECURE_URLS', True)
        self.location = location or current_app.config.get('AWS_LOCATION', '')
        self.location = self.location.lstrip('/')
        self.file_name_charset = file_name_charset or \
            current_app.config.get('AWS_S3_FILE_NAME_CHARSET', 'utf-8')

        self._connection = None
        self._entries = {}

    @property
    def connection(self):
        if self._connection is None:
            self._connection = S3Connection(
                self.access_key, self.secret_key,
                calling_format=self.calling_format
            )
        return self._connection

    @property
    def folder_name(self):
        return self.bucket_name

    @property
    def bucket(self):
        """
        Get the current bucket. If there is no current bucket object
        create it.
        """
        if not hasattr(self, '_bucket'):
            self._bucket = self._get_or_create_bucket(self.bucket_name)
        return self._bucket

    def list_folders(self):
        return [bucket.name for bucket in self.connection.get_all_buckets()]

    @property
    def folder(self):
        return self.bucket

    def list_files(self):
        return [
            self.file_class(self, key.name) for key in self.bucket.list()
        ]

    def create_folder(self, name=None):
        if not name:
            name = self.folder_name
        try:
            bucket = self.connection.create_bucket(name)
            bucket.set_acl(self.bucket_acl)
        except S3CreateError, e:
            reraise(e)
        return bucket

    def _get_or_create_bucket(self, name):
        """Retrieves a bucket if it exists, otherwise creates it."""
        try:
            return self.connection.get_bucket(
                name,
                validate=self.auto_create_bucket
            )
        except S3ResponseError:
            if self.auto_create_bucket:
                bucket = self.connection.create_bucket(name)
                bucket.set_acl(self.bucket_acl)
                return bucket
            raise RuntimeError(
                "Bucket specified by "
                "S3_BUCKET_NAME does not exist. "
                "Buckets can be automatically created by setting "
                "AWS_AUTO_CREATE_BUCKET=True")

    def _save(self, name, content):
        cleaned_name = self._clean_name(name)
        name = self._normalize_name(cleaned_name)
        headers = self.headers.copy()
        name = cleaned_name
        content_type = mimetypes.guess_type(name)[0] or Key.DefaultContentType
        encoded_name = self._encode_name(name)

        key = self.bucket.new_key(encoded_name)
        if self.preload_metadata:
            self._entries[encoded_name] = key

        key.set_metadata('Content-Type', content_type)
        if isinstance(content, basestring):
            key.set_contents_from_string(
                content,
                headers=headers,
                policy=self.acl,
                reduced_redundancy=self.reduced_redundancy
            )
        else:
            content.name = cleaned_name
            key.set_contents_from_file(
                content,
                headers=headers,
                policy=self.acl,
                reduced_redundancy=self.reduced_redundancy
            )
        return self.open(encoded_name)

    def _open(self, name, mode='r'):
        return self.file_class(self, name=name, mode=mode)

    def delete_folder(self, name=None):
        if name is None:
            name = self.folder_name
        self.bucket.delete()

    def delete(self, name):
        name = self._encode_name(self._normalize_name(self._clean_name(name)))

        if self.bucket.lookup(name) is None:
            raise FileNotFoundError(name, 404)

        self.bucket.delete_key(name)

    def exists(self, name):
        name = self._normalize_name(self._clean_name(name))
        return bool(self.bucket.lookup(self._encode_name(name)))

    def url(self, name):
        name = self._normalize_name(self._clean_name(name))

        if self.custom_domain:
            return "%s://%s/%s" % ('https' if self.secure_urls else 'http',
                                   self.custom_domain, name)
        return self.connection.generate_url(
            self.querystring_expire,
            method='GET',
            bucket=self.bucket.name,
            key=self._encode_name(name),
            query_auth=self.querystring_auth,
            force_http=not self.secure_urls
        )

    @property
    def file_class(self):
        return S3BotoStorageFile


def require_opening(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self._is_open:
            self._key.open(self._mode)
            self._is_open = True
        return func(self, *args, **kwargs)
    return wrapper


class S3BotoStorageFile(StorageFile):
    def __init__(self, storage, name=None, prefix='', mode='r'):
        if mode == 'rb':
            mode = 'r'  # rb is not supported

        self._storage = storage
        self.prefix = prefix
        self._key = Key(storage.bucket)
        self._mode = mode
        if name is not None:
            self.name = name
        self._pos = 0
        self._is_open = False

    @property
    def content_type(self):
        return getattr(
            self._key.content,
            'content_type',
            mimetypes.guess_type(self.name)[0] or Key.DefaultContentType
        )

    @property
    def file(self):
        return self._key

    @property
    @require_opening
    def size(self):
        return self._key.size

    @property
    @require_opening
    def last_modified(self):
        return self._key.last_modified

    @property
    def url(self):
        return self._storage.url(self._key.name)

    @StorageFile.name.setter
    def name(self, value):
        if self._name:
            raise StorageException(
                "You can't rename files this way. Use rename method instead."
            )
        self._name = self.prefix + self._storage._clean_name(value)
        self._key.name = self._name

    @require_opening
    def read(self, size=0):
        return self.file.read(size)

    def seek(self, *args, **kw):
        raise NotImplementedError

    def write(self, *args, **kw):
        raise NotImplementedError
