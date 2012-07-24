from flexmock import flexmock
from boto.s3.connection import S3Connection
from tests import TestCase
from flask_storage import S3BotoStorage


class MockBucket(object):
    def set_acl(self, acl):
        pass


class TestS3BotoStorage(TestCase):
    def test_assigns_folder_on_initialization(self):
        flexmock(S3Connection) \
            .should_receive('__init__') \
            .and_return(None)

        storage = S3BotoStorage('some bucket')
        assert storage.folder_name == 'some bucket'

    def test_create_folder_tries_to_create_s3_bucket(self):
        flexmock(S3Connection) \
            .should_receive('__init__') \
            .and_return(None)

        flexmock(S3Connection) \
            .should_receive('create_bucket') \
            .with_args('some_folder') \
            .and_return(MockBucket())

        storage = S3BotoStorage()
        storage.create_folder('some_folder')
