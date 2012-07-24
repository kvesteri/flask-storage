from tests import TestCase
from flask_storage import MockStorage


class TestMockStorageInit(TestCase):
    def test_assigns_folder_on_initialization(self):
        storage = MockStorage('uploads')
        assert storage.folder_name == 'uploads'


class TestMockStorageSave(TestCase):
    def test_saves_key_value_pair_in_dict(self):
        storage = MockStorage()
        storage.save('key', 1)
        assert storage.exists('key')
