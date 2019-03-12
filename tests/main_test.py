from __future__ import absolute_import

import mock
import pytest

from detect_secrets_server.__main__ import main
from detect_secrets_server.storage.base import BaseStorage
from testing.mocks import mock_git_calls
from testing.mocks import SubprocessMock
from testing.util import cache_buster


class TestMain(object):

    def teardown(self):
        cache_buster()

    def test_no_args(self):
        with pytest.raises(SystemExit):
            main([])

    @pytest.mark.parametrize(
        'argument_string,action_executed',
        [
            (
                'add examples/repos.yaml --config '
                '--storage s3 '
                '--s3-config examples/s3.yaml',
                'initialize',
            ),
            (
                'add git@github.com:yelp/detect-secrets '
                '--s3-credentials-file examples/aws_credentials.json '
                '--s3-bucket pail '
                '--storage s3',
                'add_repo',
            ),
            (
                'scan yelp/detect-secrets',
                'scan_repo',
            ),
        ]
    )
    def test_actions(self, argument_string, action_executed):
        """All detailed actions tests are covered in their individual
        test cases. This just makes sure they run, for coverage.
        """
        with mock.patch(
            'detect_secrets_server.__main__.actions',
            autospec=True,
        ) as mock_actions, mock.patch(
            'detect_secrets_server.core.usage.s3.should_enable_s3_options',
            return_value=True,
        ), mock.patch(
            'detect_secrets_server.core.usage.common.storage.should_enable_s3_options',
            return_value=True,
        ):
            mock_actions.initialize.return_value = ''
            mock_actions.scan_repo.return_value = 0

            assert main(argument_string.split()) == 0
            assert getattr(mock_actions, action_executed).called

    @pytest.mark.parametrize(
        'repo_to_scan',
        (
            'Yelp/detect-secrets',
            'https://github.com/Yelp/detect-secrets',
            'git@github.com:Yelp/detect-secrets',
        ),
    )
    def test_repositories_added_can_be_scanned(self, mock_rootdir, repo_to_scan):
        directory = '{}/repos/{}'.format(
            mock_rootdir,
            BaseStorage.hash_filename('Yelp/detect-secrets'),
        )
        mocked_sha = 'aabbcc'

        # We don't **actually** want to clone the repo per test run.
        with mock_git_calls(
            SubprocessMock(
                expected_input=(
                    'git clone https://github.com/Yelp/detect-secrets {} --bare'
                ).format(
                    directory,
                ),
            ),
            # Since there is no prior sha to retrieve
            SubprocessMock(
                expected_input='git rev-parse HEAD',
                mocked_output=mocked_sha,
            )
        ):
            assert main([
                'add', 'https://github.com/Yelp/detect-secrets',
                '--root-dir', mock_rootdir,
            ]) == 0

        with mock_git_calls(
            # Getting latest changes
            SubprocessMock(
                expected_input='git rev-parse --abbrev-ref HEAD',
                mocked_output='master',
            ),
            SubprocessMock(
                expected_input='git fetch --quiet origin master',
            ),
            # Getting relevant diff
            SubprocessMock(
                expected_input='git diff {} HEAD --name-only --diff-filter ACM'.format(mocked_sha),
                mocked_output='filenameA',
            ),
            SubprocessMock(
                expected_input='git diff {} HEAD -- filenameA'.format(mocked_sha),
                mocked_output='',
            ),
            # Storing latest sha
            SubprocessMock(
                expected_input='git rev-parse HEAD',
            ),
        ):
            assert main([
                'scan', repo_to_scan,
                '--root-dir', mock_rootdir,
            ]) == 0
