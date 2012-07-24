from tests import TestCase
from flask_storage import MockStorage, MockStorageFile


class TestMockStorage(TestCase):
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
        assert storage.url('key') == 'url-key'

    def test_open_returns_file_object(self):
        storage = MockStorage()
        storage.save('key', 1)
        file_ = storage.open('key')
        assert isinstance(file_, MockStorageFile)


class TestMockStorageFile(TestCase):
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
