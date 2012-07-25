import os
import shutil
from pytest import raises

from tests import TestCase
from flask_storage import (
    FileSystemStorage,
    FileSystemStorageFile,
    StorageException
)


class FileSystemTestCase(TestCase):
    def setup_method(self, method):
        TestCase.setup_method(self, method)
        self.path = os.path.join(
            os.path.dirname(__file__),
            'uploads',
            'images'
        )
        self.rel_path = os.path.join('uploads', 'images')

    def teardown_method(self, method):
        shutil.rmtree(os.path.join(
            os.path.dirname(__file__),
            'uploads'
        ), ignore_errors=True)


class TestFileSystemDefaults(FileSystemTestCase):
    def test_if_folder_not_set_uses_application_config_default(self):
        self.app.config['UPLOADS_FOLDER'] = self.path
        storage = FileSystemStorage()
        assert self.rel_path in storage.folder_name


class TestFileSystemCreateFolder(FileSystemTestCase):
    def teardown_method(self, method):
        FileSystemTestCase.teardown_method(self, method)
        try:
            os.remove(os.path.join(
                os.path.dirname(__file__),
                'uploads')
            )
        except OSError:
            pass

    def test_creates_folder_on_success(self):
        storage = FileSystemStorage(os.path.dirname(__file__))
        assert not os.path.exists(self.rel_path)
        storage.create_folder(self.rel_path)
        assert os.path.exists(self.path)

    def test_raises_exception_on_folder_conflict(self):
        storage = FileSystemStorage(os.path.dirname(__file__))
        storage.create_folder(self.rel_path)
        with raises(StorageException):
            storage.create_folder(self.rel_path)

    def test_raises_exception_on_file_conflict(self):
        storage = FileSystemStorage(os.path.dirname(__file__))
        storage.save('uploads', 'some text')
        with raises(StorageException):
            storage.create_folder('uploads')

    def test_conflict_exception_contains_proper_status_code(self):
        storage = FileSystemStorage(os.path.dirname(__file__))
        storage.save('uploads', 'some text')
        try:
            storage.create_folder('uploads')
            assert False
        except StorageException, e:
            assert e.status_code == 409
            assert e.message


class TestFileSystemDeleteFolder(FileSystemTestCase):
    def test_deletes_folder_on_success(self):
        storage = FileSystemStorage(os.path.dirname(__file__))
        storage.create_folder(self.rel_path)
        storage.delete_folder(self.rel_path)
        assert not os.path.exists(self.rel_path)

    def test_raises_exception_if_folder_does_not_exist(self):
        storage = FileSystemStorage(os.path.dirname(__file__))
        with raises(StorageException):
            storage.delete_folder(self.rel_path)


class TestFileSystemListFolders(FileSystemTestCase):
    def test_returns_list_of_folders_on_success(self):
        storage = FileSystemStorage(os.path.dirname(__file__))
        storage.create_folder('uploads')
        assert 'uploads' in storage.list_folders()


class TestFileSystemListFiles(FileSystemTestCase):
    def test_returns_list_of_files_on_success(self):
        storage = FileSystemStorage(os.path.dirname(__file__))
        assert os.path.basename(__file__) in storage.list_files()


class TestFileSystemOpen(FileSystemTestCase):
    def setup_method(self, method):
        FileSystemTestCase.setup_method(self, method)
        self.storage = FileSystemStorage(os.path.dirname(__file__))
        self.file = 'some_file.txt'

    def teardown_method(self, method):
        FileSystemTestCase.teardown_method(self, method)
        try:
            self.storage.delete(self.file)
        except StorageException:
            pass

    def test_raises_exception_for_unknown_file(self):
        with raises(StorageException):
            self.storage.open('some_unknown_file', 'rb')

    def test_returns_file_object_on_success(self):
        storage = FileSystemStorage(os.path.dirname(__file__))
        storage.save(self.file, 'something')
        file_ = storage.open(self.file, 'rb')
        assert isinstance(file_, FileSystemStorageFile)


class TestFileSystemDelete(FileSystemTestCase):
    def test_raises_exception_for_unknown_file(self):
        storage = FileSystemStorage(os.path.dirname(__file__))
        with raises(StorageException):
            storage.delete('some_unknown_file')
