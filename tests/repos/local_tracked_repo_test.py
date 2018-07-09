from __future__ import absolute_import

import json
import os

import mock
import pytest

from detect_secrets_server.repos.local_tracked_repo import LocalTrackedRepo
from testing.mocks import mock_git_calls
from testing.mocks import SubprocessMock


class TestLocalTrackedRepo(object):

    def test_cron(self, mock_logic):
        with mock_git_calls(
            SubprocessMock(
                expected_input='git remote get-url origin',
                mocked_output='git@github.com:yelp/detect-secrets',
            ),
        ):
            assert mock_logic.cron() == (
                '1 2 3 4 5    detect-secrets-server '
                '--scan-repo yelp/detect-secrets '
                '--local'
            )


@pytest.fixture
def mock_logic(mock_tracked_repo_data):
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
            os.path.expanduser('~/.detect-secrets-server'),
        )
