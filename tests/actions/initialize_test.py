from __future__ import absolute_import

import os
from contextlib import contextmanager

import mock
import pytest

from detect_secrets_server.actions import add_repo
from detect_secrets_server.actions import initialize
from detect_secrets_server.core.usage.parser import ServerParserBuilder
from detect_secrets_server.storage.base import BaseStorage
from testing.factories import metadata_factory
from testing.factories import single_repo_config_factory
from testing.mocks import mock_git_calls
from testing.mocks import SubprocessMock
from testing.util import cache_buster


class TestInitialize(object):

    def teardown(self):
        cache_buster()

    @staticmethod
    def parse_args(argument_string='', has_s3=False):
        base_argument = (
            'add will_be_mocked --config '
        )
        if has_s3:
            base_argument += '--s3-config examples/s3.yaml '

        with mock.patch(
            'detect_secrets_server.core.usage.s3.should_enable_s3_options',
            return_value=has_s3,
        ):
            return ServerParserBuilder().parse_args(
                (base_argument + argument_string).split()
            )

    def test_no_tracked_repos(self):
        with mock_repos_config({
            'tracked': [],
        }):
            args = self.parse_args()

        assert not initialize(args)

    def test_simple_success(self, mock_rootdir):
        with mock_repos_config({
            'tracked': [
                single_repo_config_factory(
                    'git@github.com:yelp/detect-secrets',
                ),
            ]
        }), mock_repo_class(
            'BaseTrackedRepo'
        ) as repo_class:
            args = self.parse_args(
                '--root-dir {}'.format(mock_rootdir)
            )
            initialize(args)

            repo_class.assert_called_with(
                repo='git@github.com:yelp/detect-secrets',
                sha='',
                crontab='0 0 * * *',
                plugins={
                    'AWSKeyDetector': {},
                    'ArtifactoryDetector': {},
                    'Base64HighEntropyString': {
                        'base64_limit': 4.5,
                    },
                    'BasicAuthDetector': {},
                    'HexHighEntropyString': {
                        'hex_limit': 3,
                    },
                    'JwtTokenDetector': {},
                    'MailchimpDetector': {},
                    'KeywordDetector': {
                        'keyword_exclude': None,
                    },
                    'PrivateKeyDetector': {},
                    'SlackDetector': {},
                    'StripeDetector': {},
                },
                rootdir=mock_rootdir,
                baseline_filename=None,
                # exclude_regex=None,
                exclude_files_regex=None,
                exclude_lines_regex=None,
                s3_config=None,
            )

    @pytest.mark.parametrize(
        'data,expected_repo_class',
        [
            (
                {
                    'is_local_repo': True,
                    'repo': 'examples',
                },
                'LocalTrackedRepo',
            ),
            (
                {
                    'storage': 's3',
                    'repo': 'git@github.com:yelp/detect-secrets',
                },
                'S3TrackedRepo',
            ),
            (
                {
                    'is_local_repo': True,
                    'repo': 'examples',
                    'storage': 's3',
                },
                'S3LocalTrackedRepo',
            ),
        ]
    )
    def test_flags_set_tracked_repo_classes(self, data, expected_repo_class):
        with mock_repos_config({
            'tracked': [
                single_repo_config_factory(
                    **data
                ),
            ]
        }):
            args = self.parse_args(has_s3=data.get('storage') == 's3')

        with mock_repo_class(expected_repo_class) as repo_class:
            initialize(args)
            assert repo_class.called

    def test_repo_config_overrides_defaults(self, mock_rootdir):
        with mock_repos_config({
            'tracked': [
                single_repo_config_factory(
                    'git@github.com:yelp/detect-secrets',
                    plugins={
                        # This checks that CLI overrides config file
                        'HexHighEntropyString': {
                            'hex_limit': 5,
                        },

                        # This checks it overrides default values
                        'Base64HighEntropyString': {
                            'base64_limit': 2,
                        },

                        # This checks for disabling functionality
                        'PrivateKeyDetector': False,
                    },

                    # This checks it overrides CLI (non-plugin)
                    baseline_filename='will_be_overriden',

                    # This checks it overrides default value (non-plugin)
                    # exclude_regex='something_here',
                    exclude_files_regex='something here',
                    exclude_lines_regex='something else here',
                    crontab='* * 4 * *',
                )
            ],
        }):
            args = self.parse_args(
                '--hex-limit 4 '
                '--baseline baseline.file '
                '--root-dir {}'.format(mock_rootdir)
            )

        with mock_repo_class('BaseTrackedRepo') as repo_class:
            initialize(args)

            repo_class.assert_called_with(
                repo='git@github.com:yelp/detect-secrets',
                sha='',
                crontab='* * 4 * *',
                plugins={
                    # (No PrivateKeyDetector due to being False above)
                    'ArtifactoryDetector': {},
                    'AWSKeyDetector': {},
                    'Base64HighEntropyString': {
                        'base64_limit': 2.0,
                    },
                    'BasicAuthDetector': {},
                    'HexHighEntropyString': {
                        'hex_limit': 4.0,
                    },
                    'JwtTokenDetector': {},
                    'MailchimpDetector': {},
                    'KeywordDetector': {
                        'keyword_exclude': None,
                    },
                    'SlackDetector': {},
                    'StripeDetector': {},
                },
                rootdir=mock_rootdir,
                baseline_filename='baseline.file',
                # exclude_regex='something_here',
                exclude_files_regex='something here',
                exclude_lines_regex='something else here',
                s3_config=None,
            )


class TestAddRepo(object):

    @staticmethod
    def parse_args(argument_string='', has_s3=False):
        with mock.patch(
            'detect_secrets_server.core.usage.s3.should_enable_s3_options',
            return_value=has_s3,
        ):
            return ServerParserBuilder().parse_args(
                argument_string.split()
            )

    def teardown(self):
        cache_buster()

    def test_add_non_local_repo(self, mock_file_operations, mock_rootdir):
        self.add_non_local_repo(mock_rootdir)
        mock_file_operations.write.assert_called_with(
            metadata_factory(
                repo='git@github.com:yelp/detect-secrets',
                sha='mocked_sha',
                json=True,
            ),
        )

    def test_never_override_meta_tracking_if_already_exists(
        self,
        mock_file_operations,
        mock_rootdir,
    ):
        with mock.patch(
            'detect_secrets_server.storage.file.FileStorage.get_tracked_file_location',

            # This doesn't matter what it is, just that it exists.
            return_value='examples/config.yaml',
        ):
            self.add_non_local_repo(mock_rootdir)

        assert not mock_file_operations.write.called

    def add_non_local_repo(self, mock_rootdir):
        repo = 'git@github.com:yelp/detect-secrets'
        directory = '{}/repos/{}'.format(
            mock_rootdir,
            BaseStorage.hash_filename('yelp/detect-secrets'),
        )

        git_calls = [
            SubprocessMock(
                expected_input='git clone {} {} --bare'.format(repo, directory),
            ),
            SubprocessMock(
                expected_input='git rev-parse HEAD',
                mocked_output='mocked_sha',
            ),
        ]

        with mock_git_calls(*git_calls):
            args = self.parse_args('add {} --root-dir {}'.format(repo, mock_rootdir))
            add_repo(args)

    def test_add_local_repo(self, mock_file_operations, mock_rootdir):
        # This just needs to exist; no actual operations will be done to this.
        repo = 'examples'

        git_calls = [
            # repo.update
            SubprocessMock(
                expected_input='git rev-parse HEAD',
                mocked_output='mocked_sha',
            ),
        ]

        with mock_git_calls(*git_calls):
            args = self.parse_args(
                'add {} --baseline .secrets.baseline --local --root-dir {}'.format(
                    repo,
                    mock_rootdir,
                )
            )

            add_repo(args)

        mock_file_operations.write.assert_called_with(
            metadata_factory(
                sha='mocked_sha',
                repo=os.path.abspath(
                    os.path.join(
                        os.path.dirname(__file__),
                        '../../examples',
                    ),
                ),
                baseline_filename='.secrets.baseline',
                json=True,
            ),
        )

    def test_add_s3_backend_repo(self, mock_file_operations, mocked_boto):
        args = self.parse_args(
            'add {} '
            '--local '
            '--storage s3 '
            '--s3-credentials-file examples/aws_credentials.json '
            '--s3-bucket pail'.format('examples'),
            has_s3=True,
        )

        git_calls = [
            # repo.update
            SubprocessMock(
                expected_input='git rev-parse HEAD',
                mocked_output='mocked_sha',
            ),
        ]

        with mock_git_calls(
            *git_calls
        ):
            mocked_boto.list_objects_v2.return_value = {}
            add_repo(args)


@contextmanager
def mock_repos_config(data):
    """Unfortunately, mocking this means that we can't test more than
    one config file at a time. However, all consolidation tests with
    --config-file should have been done in usage_test, so we should
    be OK.
    """
    with mock.patch(
        'detect_secrets_server.core.usage.add.config_file',
        return_value=data,
    ):
        yield


@contextmanager
def mock_repo_class(classname):
    """
    :type classname: str
    """
    with mock.patch(
        'detect_secrets_server.repos.factory.{}'.format(classname),
    ) as repo_class:
        yield repo_class
