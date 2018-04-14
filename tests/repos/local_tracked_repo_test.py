from __future__ import absolute_import

import json
import os

import mock

from .base_tracked_repo_test import mock_tracked_repo_data as \
    _mock_tracked_repo_data
from detect_secrets_server.repos.local_tracked_repo import LocalTrackedRepo
from tests.util.mock_util import mock_git_calls
from tests.util.mock_util import SubprocessMock


class TestLocalTrackedRepo(object):

    def test_cron(self):
        repo = mock_logic()

        with mock_git_calls(
            SubprocessMock(
                expected_input='git remote get-url origin',
                mocked_output='git@github.com:yelp/detect-secrets',
            ),
        ):
            assert repo.cron() == (
                '1 2 3 4 5    detect-secrets-server '
                '--scan-repo yelp/detect-secrets '
                '--local'
            )


def mock_logic():
    mock_open = mock.mock_open(read_data=json.dumps(
        mock_tracked_repo_data(),
    ))

    with mock.patch(
        'detect_secrets_server.storage.file.open',
        mock_open,
    ):
        return LocalTrackedRepo.load_from_file(
            'will_be_mocked',
            os.path.expanduser('~/.detect-secrets-server'),
        )


def mock_tracked_repo_data():
    data = _mock_tracked_repo_data()
    data['repo'] = 'does_not_matter'

    return data
