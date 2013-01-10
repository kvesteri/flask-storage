from __future__ import absolute_import

import mimetypes
import cloudfiles
from cloudfiles.errors import NoSuchObject, ResponseError, NoSuchContainer
from flask import current_app, request
from werkzeug.utils import cached_property

from .base import Storage, StorageFile, reraise

__all__ = ('CloudFilesStorage',)


class CloudFilesStorage(Storage):
    def __init__(self,
                 folder_name=None,
                 username=None,
                 api_key=None,
                 timeout=None):
        """
        Initialize the settings for the connection and container.
        """
        self.username = username or current_app.config.get(
            'CLOUDFILES_USERNAME', None)
        self.api_key = api_key or current_app.config.get(
            'CLOUDFILES_API_KEY', None)
        self.container_name = folder_name or \
            current_app.config.get('CLOUDFILES_CONTAINER', None)
        self.timeout = timeout or current_app.config.get(
            'CLOUDFILES_TIMEOUT', 5)
        self.use_servicenet = current_app.config.get(
            'CLOUDFILES_SERVICENET', False)
        self.auto_create_container = current_app.config.get(
            'CLOUDFILES_AUTO_CREATE_CONTAINER', False)
        self.secure_uris = current_app.config.get(
            'CLOUDFILES_SECURE_URIS', False)

    @property
    def folder_name(self):
        return self.container_name

    @property
    def folder(self):
        return self.container

    @cached_property
    def connection(self):
        return cloudfiles.get_connection(
            username=self.username,
            api_key=self.api_key,
            timeout=self.timeout,
            servicenet=self.use_servicenet
        )

    @property
    def container(self):
        if not hasattr(self, '_container'):
            self._container = self._get_or_create_container(self.container_name)
        if not self._container.is_public():
            self._container.make_public()
        return self._container

    @cached_property
    def container_url(self):
        container_uris = current_app.config.get(
            'CLOUDFILES_CONTAINER_URIS', {})
        if self.container_name in container_uris:
            return container_uris[self.container_name]
        if self.secure_uris or request.is_secure:
            return self.container.public_ssl_uri()
        else:
            return self.container.public_uri()

    def _get_or_create_container(self, name):
        """Retrieves a bucket if it exists, otherwise creates it."""
        try:
            return self.connection.get_container(name)
        except NoSuchContainer:
            if self.auto_create_container:
                return self.connection.create_container(name)
            else:
                raise RuntimeError(
                    "Container specified by "
                    "CLOUDFILES_BUCKET_NAME does not exist. "
                    "Containers can be automatically created by setting "
                    "CLOUDFILES_AUTO_CREATE_CONTAINER=True")

    def _save(self, name, content):
        """
        Use the Cloud Files service to write a `werkzeug.FileStorage`
        (called ``file``) to a remote file (called ``name``).
        """
        cloud_obj = self.container.create_object(name)
        mimetype, _ = mimetypes.guess_type(name)
        cloud_obj.content_type = mimetype
        cloud_obj.send(content)
        return self.open(name)

    def _open(self, name, mode='rb'):
        return self.file_class(self, name)

    def delete(self, name):
        """
        Deletes the specified file from the storage system.
        """
        try:
            self.container.delete_object(name)
        except ResponseError, e:
            reraise(e)

    def exists(self, name):
        """
        Returns True if a file referenced by the given name already exists in
        the storage system, or False if the name is available for a new file.
        """
        try:
            self.container.get_object(name)
            return True
        except NoSuchObject:
            return False

    def url(self, name):
        """
        Returns an absolute URL where the file's contents can be accessed
        directly by a web browser.
        """
        return '%s/%s' % (self.container_url, name)

    def get_object(self, name):
        try:
            return self.container.get_object(name)
        except NoSuchObject, e:
            reraise(e)
        except ResponseError, e:
            reraise(e)

    @property
    def file_class(self):
        return CloudFilesStorageFile


class CloudFilesStorageFile(StorageFile):
    _file = None

    def __init__(self, storage, name=None, prefix=''):
        self._storage = storage
        self.prefix = prefix
        if name is not None:
            self.name = name
        if self._name:
            self.file
        self._pos = 0

    @property
    def file(self):
        if not self._file:
            self._file = self._storage.get_object(self.name)
        return self._file

    def read(self, size=-1, **kw):
        kw['offset'] = self._pos
        data = self.file.read(size, **kw)
        self._pos += len(data)
        return data
