import os
import shutil
from pytest import raises

from tests import TestCase
from flask_storage import FileSystemStorage, StorageException


class TestFileSystemDefaults(TestCase):
    def test_if_folder_not_set_uses_application_config_default(self):
        self.app.config['UPLOADS_FOLDER'] = 'uploads'
        storage = FileSystemStorage()
        assert 'uploads' in storage.folder_name


class TestFileSystemCreateFolder(TestCase):
    def teardown_method(self, method):
        try:
            shutil.rmtree('uploads/images')
        except OSError:
            pass

    def test_creates_folder_on_success(self):
        assert not os.path.exists('uploads/images')
        storage = FileSystemStorage(os.path.dirname(__file__))
        storage.create_folder('uploads/images')
        assert os.path.exists('uploads/images')


class TestFileSystemDelete(TestCase):
    def test_raises_exception_for_unknown_file(self):
        storage = FileSystemStorage(os.path.dirname(__file__))
        with raises(StorageException):
            storage.delete('some_unknown_file')
