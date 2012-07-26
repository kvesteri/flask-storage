from pytest import raises

from flexmock import flexmock
import cloudfiles
from tests import TestCase
from flask_storage import (
    CloudFilesStorage,
    CloudFilesStorageFile,
    StorageException
)


class MockConnection(object):
    def get_container(self, name):
        return MockContainer()


class MockContainer(object):
    objects = {}

    def delete_object(self, name):
        raise cloudfiles.errors.ResponseError(
            status=404,
            reason='some reason'
        )

    def create_object(self, name):
        obj = MockCloubObject()
        self.objects[name] = obj
        return obj

    def get_object(self, name):
        if name not in self.objects:
            raise cloudfiles.errors.NoSuchObject()
        return self.objects[name]


class MockCloubObject(object):
    def send(self, content):
        self.content = content


class TestCloudFilesStorage(TestCase):
    def setup_method(self, method):
        TestCase.setup_method(self, method)

    def test_delete_raises_exception_for_unknown_file(self):
        flexmock(cloudfiles).should_receive('get_connection') \
            .and_return(MockConnection())
        self.storage = CloudFilesStorage()
        with raises(StorageException):
            self.storage.delete('key')

    def test_open_raises_exception_for_unknown_object(self):
        flexmock(cloudfiles).should_receive('get_connection') \
            .and_return(MockConnection())
        self.storage = CloudFilesStorage()
        with raises(StorageException):
            self.storage.open('some_unknown_object')

    def test_open_returns_file_object_on_success(self):
        flexmock(cloudfiles).should_receive('get_connection') \
            .and_return(MockConnection())
        self.storage = CloudFilesStorage()
        self.storage.save('key', 'something')
        obj = self.storage.open('key')
        assert isinstance(obj, CloudFilesStorageFile)

    def test_save_creates_new_object(self):
        flexmock(cloudfiles).should_receive('get_connection') \
            .and_return(MockConnection())
        self.storage = CloudFilesStorage()
        self.storage.save('key', 'something')
        self.storage.exists('key')
