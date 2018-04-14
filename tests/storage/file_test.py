from __future__ import absolute_import

import json
import os

import mock
import pytest

from .base_test import assert_directories_created
from detect_secrets_server.storage.file import FileStorage
from detect_secrets_server.storage.file import FileStorageWithLocalGit


class TestFileStorage(object):

    def logic(self):
        return FileStorage(
            os.path.expanduser('~/.detect-secrets-server'),
        )

    def test_setup_creates_directories(self):
        with assert_directories_created([
            '~/.detect-secrets-server',
            '~/.detect-secrets-server/repos',
            '~/.detect-secrets-server/tracked',
        ]):
            self.logic().setup('git@github.com:yelp/detect-secrets')

    def test_get_success(self):
        mocked_data = {'key': 'value'}
        mock_open = mock.mock_open(read_data=json.dumps(mocked_data))
        with mock.patch('builtins.open', mock_open):
            data = self.logic().get('does_not_matter')

        assert data == {'key': 'value'}

    def test_get_failure(self):
        with pytest.raises(FileNotFoundError):
            self.logic().get('file_does_not_exist')

    def test_put_success(self):
        mock_open = mock.mock_open()
        with mock.patch('builtins.open', mock_open):
            self.logic().put('filename', {
                'key': 'value',
            })

        mock_open().write.assert_called_with(
            json.dumps(
                {
                    'key': 'value',
                },
                indent=2,
            )
        )


class TestFileStorageWithLocalGit(object):

    def logic(self):
        return FileStorageWithLocalGit(
            os.path.expanduser('~/.detect-secrets-server'),
        )

    def test_setup_creates_directories(self):
        with assert_directories_created([
            '~/.detect-secrets-server',
            '~/.detect-secrets-server/tracked',
            '~/.detect-secrets-server/tracked/local',
        ]):
            self.logic().setup('git@github.com:yelp/detect-secrets')

    def test_get_success(self):
        mock_open = mock.mock_open(read_data='{}')
        with mock.patch('builtins.open', mock_open):
            self.logic().get('mock_filename')

        mock_open.assert_called_with(
            os.path.expanduser(
                '~/.detect-secrets-server/tracked/local/mock_filename.json'
            ),
        )
