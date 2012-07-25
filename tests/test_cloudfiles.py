from pytest import raises

from flexmock import flexmock
import cloudfiles
from tests import TestCase
from flask_storage import (
    CloudFilesStorage,
    StorageException
)


class MockConnection(object):
    def get_container(self, name):
        return MockContainer()


class MockContainer(object):
    def delete_object(self, name):
        raise cloudfiles.errors.ResponseError(status=404, reason='some reason')


class TestCloudFilesStorage(TestCase):
    def test_delete_raises_exception_for_unknown_file(self):
        flexmock(cloudfiles).should_receive('get_connection') \
            .and_return(MockConnection())
        storage = CloudFilesStorage()
        with raises(StorageException):
            storage.delete('key')
