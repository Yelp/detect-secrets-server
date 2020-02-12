import json

import pytest

from .base_test import assert_directories_created
from detect_secrets_server.storage.file import FileStorage
from detect_secrets_server.storage.file import FileStorageWithLocalGit
from testing.mocks import mock_open


@pytest.fixture
def file_storage(mock_rootdir):
    return FileStorage(mock_rootdir)


@pytest.fixture
def local_file_storage(mock_rootdir):
    return FileStorageWithLocalGit(mock_rootdir)


class TestFileStorage(object):

    def test_setup_creates_directories(self, file_storage, mock_rootdir):
        with assert_directories_created([
            mock_rootdir,
            mock_rootdir + '/repos',
            mock_rootdir + '/tracked',
        ]):
            file_storage.setup('git@github.com:yelp/detect-secrets')

    def test_get_success(self, file_storage):
        with mock_open({'key': 'value'}):
            data = file_storage.get('does_not_matter')

        assert data == {'key': 'value'}

    def test_get_failure(self, file_storage):
        with pytest.raises(FileNotFoundError):
            file_storage.get('file_does_not_exist')

    def test_put_success(self, file_storage):
        with mock_open() as m:
            file_storage.put('filename', {
                'key': 'value',
            })

            m().write.assert_called_with(
                json.dumps(
                    {
                        'key': 'value',
                    },
                    indent=2,
                    sort_keys=True,
                )
            )


class TestFileStorageWithLocalGit(object):

    def test_setup_creates_directories(self, local_file_storage, mock_rootdir):
        with assert_directories_created([
            mock_rootdir,
            mock_rootdir + '/tracked',
            mock_rootdir + '/tracked/local',
        ]):
            local_file_storage.setup('git@github.com:yelp/detect-secrets')

    def test_get_success(self, local_file_storage, mock_rootdir):
        with mock_open() as m:
            local_file_storage.get('mock_filename')

            m.assert_called_with(
                '{}/tracked/local/mock_filename.json'.format(
                    mock_rootdir,
                ),
            )
