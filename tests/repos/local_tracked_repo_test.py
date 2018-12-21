from __future__ import absolute_import

import json

import mock
import pytest

from detect_secrets_server.repos.local_tracked_repo import LocalTrackedRepo


class TestLocalTrackedRepo(object):

    def test_cron(self, mock_logic):
        assert mock_logic.cron() == (
            '1 2 3 4 5    detect-secrets-server '
            'scan does_not_matter '
            '--local'
        )


@pytest.fixture
def mock_logic(mock_tracked_repo_data, mock_rootdir):
    mock_tracked_repo_data['repo'] = 'does_not_matter'

    mock_open = mock.mock_open(read_data=json.dumps(
        mock_tracked_repo_data,
    ))

    with mock.patch(
        'detect_secrets_server.storage.file.open',
        mock_open,
    ), mock.patch(
        'detect_secrets_server.storage.base.os.makedirs',
    ):
        return LocalTrackedRepo.load_from_file(
            'will_be_mocked',
            mock_rootdir,
        )
