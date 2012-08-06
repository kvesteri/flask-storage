from pytest import raises

from tests import TestCase
from flask_storage import MockStorage, MockStorageFile, FileNotFoundError


class TestMockStorage(TestCase):
    def setup_method(self, method):
        TestCase.setup_method(self, method)
        MockStorage._files = {}

    def test_assigns_folder_on_initialization(self):
        storage = MockStorage('uploads')
        assert storage.folder_name == 'uploads'

    def test_saves_key_value_pair_in_dict(self):
        storage = MockStorage()
        storage.save('key', 1)
        assert storage.exists('key')

    def test_returns_file_url(self):
        storage = MockStorage()
        storage.save('key', 1)
        assert storage.url('key') == '/uploads/key'

    def test_open_returns_file_object(self):
        storage = MockStorage()
        storage.save('key', 1)
        file_ = storage.open('key')
        assert isinstance(file_, MockStorageFile)

    def test_open_raises_excetion_for_unknown_file(self):
        storage = MockStorage()
        with raises(FileNotFoundError):
            storage.open('key')

    def test_delete_raises_exception_for_unknown_file(self):
        storage = MockStorage()
        with raises(FileNotFoundError):
            storage.delete('key')


class TestMockStorageFile(TestCase):
    def setup_method(self, method):
        TestCase.setup_method(self, method)
        MockStorage._files = {}

    def test_size_returns_the_associated_file_size(self):
        storage = MockStorage('uploads')
        storage.save('key', 123123)
        file_ = storage.open('key')
        assert file_.size == 6

    def test_read_returns_file_contents(self):
        storage = MockStorage('uploads')
        storage.save('key', 123123)
        file_ = storage.open('key')
        assert file_.read() == '123123'
