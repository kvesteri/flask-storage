from __future__ import absolute_import

import mimetypes
import cloudfiles
from cloudfiles.errors import NoSuchObject, ResponseError
from flask import current_app
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
            self._container = self.connection.get_container(
                self.container_name)
        return self._container

    @container.setter
    def container(self, container):
        """
        Set the container, making it publicly available if it is not already.
        """
        if not container.is_public():
            container.make_public()
        self._container = container

    @cached_property
    def container_url(self):
        container_uris = current_app.config.get(
            'CLOUDFILES_CONTAINER_URIS', {})
        if self.container_name in container_uris:
            return container_uris[self.container_name]
        return self.container.public_ssl_uri()

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
        return CloudFilesStorageFile(self, name)

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


class CloudFilesStorageFile(StorageFile):
    def __init__(self, storage, name):
        self._file = storage.get_object(name)
        self._name = name
        self._pos = 0

    @property
    def name(self):
        return self._name
