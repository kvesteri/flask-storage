from tests import TestCase
from flask_storage import MockStorage


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
