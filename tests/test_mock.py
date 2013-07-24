from __future__ import with_statement
from StringIO import StringIO
from pytest import raises

from tests import TestCase
from flask_storage import (
    MockStorage, MockStorageFile, StorageException, FileNotFoundError
)


class TestMockStorage(TestCase):
    def setup_method(self, method):
        TestCase.setup_method(self, method)
        MockStorage._files = {}

    def test_assigns_folder_on_initialization(self):
        storage = MockStorage('uploads')
        assert storage.folder_name == 'uploads'

    def test_saves_key_value_pair_in_dict(self):
        storage = MockStorage()
        storage.save('key', '')
        assert storage.exists('key')

    def test_save_returns_file_object_on_success(self):
        storage = MockStorage()
        obj = storage.save('key', 'value')
        assert obj.name == 'key'

    def test_save_supports_overwrite(self):
        storage = MockStorage()
        storage.save('key', 'value')
        storage.save('key', 'value 2', overwrite=True)
        assert len(MockStorage._files) == 1

    def test_reads_file_object_and_saves_in_dict(self):
        storage = MockStorage()
        io = StringIO()
        io.write('file contents')
        storage.save('key', io)
        assert storage.open('key').read() == 'file contents'

    def test_returns_file_url(self):
        storage = MockStorage('/uploads')
        storage.save('key', '')
        assert storage.url('key') == '/uploads/key'

    def test_supports_directories_in_file_names(self):
        storage = MockStorage()
        storage.save('some_dir/filename.txt', 'something')
        assert storage.open('some_dir/filename.txt').read() == 'something'

    def test_open_returns_file_object(self):
        storage = MockStorage()
        storage.save('key', '')
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

    def test_new_file(self):
        storage = MockStorage()
        assert isinstance(storage.new_file(), MockStorageFile)

    def test_new_file_supports_prefixes(self):
        storage = MockStorage()
        assert storage.new_file(prefix='pics').prefix == 'pics'


class TestMockStorageFile(TestCase):
    def setup_method(self, method):
        TestCase.setup_method(self, method)
        MockStorage._files = {}
        self.storage = MockStorage('/uploads')

    def test_size_returns_the_associated_file_size(self):
        storage = MockStorage('uploads')
        storage.save('key', '123123')
        file_ = storage.open('key')
        assert file_.size == 6

    def test_read_returns_file_contents(self):
        storage = MockStorage('uploads')
        storage.save('key', '123123')
        file_ = storage.open('key')
        assert file_.read() == '123123'

    def test_supports_file_objects_without_name(self):
        storage = MockStorage('uploads')
        file_ = MockStorageFile(storage)
        assert bool(file_) is False

    def test_returns_file_url(self):
        storage = MockStorage('/uploads')
        file_ = storage.save('key', '123123')
        assert file_.url == '/uploads/key'

    def test_supports_name_attribute(self):
        storage = MockStorage('uploads')
        file_ = MockStorageFile(storage)
        file_.name = 'some_key'
        assert file_.name == 'some_key'

    def test_rename_throws_error(self):
        storage = MockStorage('uploads')
        file_ = MockStorageFile(storage)
        file_.name = 'some_key'
        with raises(StorageException):
            file_.name = 'some_key2'

    def test_supports_save(self):
        file_ = MockStorageFile(self.storage)
        file_.name = 'some_key'
        file_.save(content='something')
        assert file_.read() == 'something'

    def test_supports_prefixes(self):
        file_ = MockStorageFile(self.storage, prefix='pics/')
        file_.name = 'some_key'
        assert file_.name == 'pics/some_key'

    def test_supports_last_modified(self):
        file_ = MockStorageFile(self.storage, prefix=u'pics/')
        file_.name = 'some_key'
        file_.last_modified

    def test_equality_operator(self):
        file_ = MockStorageFile(self.storage)
        file_.name = 'some_key'
        file2 = MockStorageFile(self.storage)
        file2.name = 'some_key'
        assert file_ == file2
        file2.rename('some other key')
        assert file_ != file2

    def test_equality_operator_with_none_values(self):
        file_ = MockStorageFile(self.storage)
        file_.name = 'some_key'
        none = None
        assert not file_ == none
        assert file_ != none
