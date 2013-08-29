from __future__ import with_statement
from datetime import datetime
from pytest import raises

from flexmock import flexmock
from boto.s3.connection import S3Connection
from boto.s3.key import Key
from boto.s3.bucket import Bucket
from tests import TestCase
from flask_storage import S3BotoStorage, S3BotoStorageFile, FileNotFoundError


class MockKey(object):
    def __init__(self, *args, **kwargs):
        pass

    def set_metadata(self, key, data):
        pass

    def set_contents_from_string(self, s, **kwargs):
        pass

    def open(self, *args, **kwargs):
        pass

    def read(self, size=-1):
        pass

    last_modified = datetime(1971, 1, 1)
    size = 0


class MockBucket(object):
    def __init__(self, *args, **kwargs):
        pass

    def set_acl(self, acl):
        pass

    def lookup(self, key):
        return None

    def delete_key(self, key):
        pass

    def new_key(self, key):
        return MockKey()

    def list(self):
        return []


def mock_s3():
    flexmock(Key).should_receive('__new__').replace_with(MockKey)
    flexmock(Bucket).should_receive('__new__').replace_with(MockBucket)
    (flexmock(S3Connection)
        .should_receive('__init__')
        .and_return(None))


class TestS3BotoStorage(TestCase):
    def setup_method(self, method):
        TestCase.setup_method(self, method)
        self.storage = S3BotoStorage()

    def test_assigns_folder_on_initialization(self):
        mock_s3()
        storage = S3BotoStorage('some bucket')
        assert storage.folder_name == 'some bucket'

    def test_create_folder_tries_to_create_s3_bucket(self):
        mock_s3()
        flexmock(S3Connection) \
            .should_receive('create_bucket') \
            .with_args('some_folder') \
            .and_return(MockBucket())
        self.storage.create_folder('some_folder')

    def test_delete_raises_file_not_found_for_unknown_file(self):
        mock_s3()
        (
            flexmock(S3Connection)
            .should_receive('get_bucket')
            .and_return(MockBucket())
        )
        storage = S3BotoStorage('some bucket')
        with raises(FileNotFoundError):
            storage.delete('key')

    def test_list_files_returns_list_of_key_names(self):
        mock_s3()
        (
            flexmock(S3Connection)
            .should_receive('get_bucket')
            .and_return(MockBucket())
        )
        storage = S3BotoStorage('some bucket')
        assert storage.list_files() == []

    def test_save_file_with_content_as_string(self):
        mock_s3()
        (
            flexmock(S3Connection)
            .should_receive('get_bucket')
            .and_return(MockBucket())
        )
        storage = S3BotoStorage('some bucket')
        storage.save('some_file', 'some content')


class TestS3BotoStorageOpenFile(TestCase):
    def test_open_returns_file_object(self):
        mock_s3()

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
        mock_s3()
        file_ = S3BotoStorageFile(self.storage, prefix='pics/')
        file_.name = 'some_key'
        assert file_.name == u'pics/some_key'

    def test_supports_last_modified(self):
        mock_s3()
        file_ = S3BotoStorageFile(self.storage, prefix='pics/')
        file_.name = 'some_key'
        file_.last_modified

    def test_supports_reading(self):
        mock_s3()
        file_ = S3BotoStorageFile(self.storage, prefix='pics/')
        file_.name = 'some_key'

        (flexmock(MockKey)
            .should_receive('read')
            .once()
            .with_args(341)
            .and_return('test data!'))

        assert file_.read(341) == 'test data!'

    def test_does_not_open_file_on_creation(self):
        mock_s3()
        (flexmock(MockKey)
            .should_receive('open')
            .never())
        S3BotoStorageFile(self.storage, prefix='pics/')

    def test_opens_file_on_size_access(self):
        mock_s3()
        (flexmock(MockKey)
            .should_receive('open')
            .once())
        file_ = S3BotoStorageFile(self.storage, prefix='pics/')
        file_.size

    def test_opens_file_on_read(self):
        mock_s3()
        (flexmock(MockKey)
            .should_receive('open')
            .once())
        file_ = S3BotoStorageFile(self.storage, prefix='pics/')
        file_.read()
