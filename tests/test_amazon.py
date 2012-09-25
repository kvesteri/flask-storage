from __future__ import with_statement
from pytest import raises

from flexmock import flexmock
from boto.s3.connection import S3Connection
from tests import TestCase
from flask_storage import S3BotoStorage, S3BotoStorageFile, StorageException


class MockBucket(object):
    def set_acl(self, acl):
        pass

    def lookup(self, key):
        return None

    def delete_key(self, key):
        pass

    def list(self):
        return []


def mock_s3_connection():
    return (
        flexmock(S3Connection)
        .should_receive('__init__')
        .and_return(None)
    )


class TestS3BotoStorage(TestCase):
    def setup_method(self, method):
        TestCase.setup_method(self, method)
        mock_s3_connection()
        self.storage = S3BotoStorage()

    def test_assigns_folder_on_initialization(self):
        mock_s3_connection()
        storage = S3BotoStorage('some bucket')
        assert storage.folder_name == 'some bucket'

    def test_create_folder_tries_to_create_s3_bucket(self):
        flexmock(S3Connection) \
            .should_receive('create_bucket') \
            .with_args('some_folder') \
            .and_return(MockBucket())
        self.storage.create_folder('some_folder')

    def test_delete_raises_exception_for_unknown_file(self):
        mock_s3_connection()
        (
            flexmock(S3Connection)
            .should_receive('get_bucket')
            .and_return(MockBucket())
        )
        storage = S3BotoStorage('some bucket')
        with raises(StorageException):
            storage.delete('key')

    def test_list_files_returns_list_of_key_names(self):
        mock_s3_connection()
        (
            flexmock(S3Connection)
            .should_receive('get_bucket')
            .and_return(MockBucket())
        )
        storage = S3BotoStorage('some bucket')
        assert storage.list_files() == []


class TestS3BotoStorageOpenFile(TestCase):
    def test_open_returns_file_object(self):
        mock_s3_connection()

        flexmock(S3BotoStorage) \
            .should_receive('_get_or_create_bucket') \
            .with_args('some_bucket') \
            .and_return(MockBucket())
        storage = S3BotoStorage('some_bucket')
        file_ = storage.open('some_file')
        assert isinstance(file_, S3BotoStorageFile)


class TestS3BotoStorageFile(TestCase):
    def setup_method(self, method):
        TestCase.setup_method(self, method)
        mock_s3_connection()
        flexmock(S3BotoStorage) \
            .should_receive('_get_or_create_bucket') \
            .with_args('some_bucket') \
            .and_return(MockBucket())

        self.storage = S3BotoStorage('some_bucket')
        self.file = S3BotoStorageFile(self.storage, 'some_file')

    def test_supports_file_objects_without_name(self):
        file_ = S3BotoStorageFile(self.storage)
        assert bool(file_) is False

    def test_supports_prefixes(self):
        file_ = S3BotoStorageFile(self.storage, prefix=u'pics/')
        file_.name = 'some_key'
        assert file_.name == u'pics/some_key'

    def test_supports_last_modified(self):
        file_ = S3BotoStorageFile(self.storage, prefix=u'pics/')
        file_.name = 'some_key'
        file_.last_modified
