from __future__ import absolute_import

import json
from contextlib import contextmanager

import mock
import pytest

from detect_secrets_server.actions import add_repo
from detect_secrets_server.actions import initialize
from detect_secrets_server.core.usage.parser import ServerParserBuilder
from detect_secrets_server.storage.base import BaseStorage
from testing.mocks import mock_git_calls
from testing.mocks import SubprocessMock


class TestInitialize(object):

    @staticmethod
    def parse_args(argument_string='', has_s3=False):
        base_argument = (
            'add will_be_mocked --config '
            '--output-hook examples/standalone_hook.py '
        )
        if has_s3:
            base_argument += '--s3-config examples/s3.yaml'

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
                self.mock_config_data()
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
                sha='afe6f0bced18a7f7d56975e6d0cdb45b95fbb4b1',
                crontab='* * 4 * *',
                plugins={
                    'HexHighEntropyString': {
                        'hex_limit': 3,
                    },
                    'Base64HighEntropyString': {
                        'base64_limit': 4.5,
                    },
                    'PrivateKeyDetector': {},
                    'BasicAuthDetector': {},
                },
                rootdir=mock_rootdir,
                baseline_filename=None,
                exclude_regex=None,
                s3_config=None,
            )

    @pytest.mark.parametrize(
        'extra_data,expected_repo_class',
        [
            (
                {
                    'is_local_repo': True,
                },
                'LocalTrackedRepo',
            ),
            (
                {
                    's3_backend': True,
                },
                'S3TrackedRepo',
            ),
            (
                {
                    'is_local_repo': True,
                    's3_backend': True,
                },
                'S3LocalTrackedRepo',
            ),
        ]
    )
    def test_flags_set_tracked_repo_classes(self, extra_data, expected_repo_class):
        with mock_repos_config({
            'tracked': [
                self.mock_config_data(extra_data)
            ]
        }):
            args = self.parse_args(has_s3=extra_data.get('s3_backend', False))

        with mock_repo_class(expected_repo_class) as repo_class:
            initialize(args)
            assert repo_class.called

    def test_repo_config_overrides_defaults(self, mock_rootdir):
        with mock_repos_config({
            'tracked': [
                self.mock_config_data({
                    'plugins': {
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
                    'baseline_filename': 'will_be_overriden',

                    # This checks it overrides default value (non-plugin)
                    'exclude_regex': 'something_here',
                })
            ]
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
                sha='afe6f0bced18a7f7d56975e6d0cdb45b95fbb4b1',
                crontab='* * 4 * *',
                plugins={
                    'HexHighEntropyString': {
                        'hex_limit': 4.0,
                    },
                    'Base64HighEntropyString': {
                        'base64_limit': 2.0,
                    },
                    'PrivateKeyDetector': False,
                    'BasicAuthDetector': {},
                },
                rootdir=mock_rootdir,
                baseline_filename='baseline.file',
                exclude_regex='something_here',
                s3_config=None,
            )

    def test_cron_output_and_file_writes(self, mock_file_operations):
        with mock_repos_config({
            'tracked': [
                self.mock_config_data(),
                self.mock_config_data({
                    'repo': 'git@github.com:yelp/detect-secrets-server',
                    'crontab': '* * 2 * *',
                    'sha': '449360c3a9a4fb76fba90a2b9de9cb5ea812726d',
                    'baseline': '.secrets.baseline',
                    'plugins': {
                        'HexHighEntropyString': {
                            'hex_limit': 2,
                        },
                    },
                    'exclude_regex': 'tests/*',
                }),
            ]
        }):
            args = self.parse_args()

        assert initialize(args) == (
            '# detect-secrets scanner\n'
            '* * 4 * *    detect-secrets-server '
            'scan yelp/detect-secrets '
            '--output-hook examples/standalone_hook.py\n'
            '* * 2 * *    detect-secrets-server '
            'scan yelp/detect-secrets-server '
            '--output-hook examples/standalone_hook.py'
        )

        mock_file_operations.write.assert_has_calls([
            mock.call(
                json.dumps({
                    'sha': 'afe6f0bced18a7f7d56975e6d0cdb45b95fbb4b1',
                    'repo': 'git@github.com:yelp/detect-secrets',
                    'plugins': {
                        'HexHighEntropyString': {
                            'hex_limit': 3,
                        },
                        'Base64HighEntropyString': {
                            'base64_limit': 4.5,
                        },
                        'PrivateKeyDetector': {},
                        'BasicAuthDetector': {},
                    },
                    'crontab': '* * 4 * *',
                    'baseline_filename': None,
                    'exclude_regex': None,
                }, indent=2, sort_keys=True)
            ),
            mock.call(
                json.dumps({
                    'sha': '449360c3a9a4fb76fba90a2b9de9cb5ea812726d',
                    'repo': 'git@github.com:yelp/detect-secrets-server',
                    'plugins': {
                        'HexHighEntropyString': {
                            'hex_limit': 2,
                        },
                        'Base64HighEntropyString': {
                            'base64_limit': 4.5,
                        },
                        'PrivateKeyDetector': {},
                        'BasicAuthDetector': {},
                    },
                    'crontab': '* * 2 * *',
                    'baseline_filename': '.secrets.baseline',
                    'exclude_regex': 'tests/*',
                }, indent=2, sort_keys=True),
            ),
        ])

    @staticmethod
    def mock_config_data(extra_data=None):
        if not extra_data:
            extra_data = {}

        required_args = {
            'repo': 'git@github.com:yelp/detect-secrets',
            'sha': 'afe6f0bced18a7f7d56975e6d0cdb45b95fbb4b1',
            'crontab': '* * 4 * *',
        }

        required_args.update(extra_data)

        return required_args


class TestAddRepo(object):

    @staticmethod
    def parse_args(argument_string='', is_s3=False):
        with mock.patch(
            'detect_secrets_server.core.usage.s3.should_enable_s3_options',
            return_value=is_s3,
        ):
            return ServerParserBuilder().parse_args(
                argument_string.split()
            )

    def test_add_non_local_repo(self, mock_file_operations, mock_rootdir):
        self.add_non_local_repo(mock_rootdir)
        mock_file_operations.write.assert_called_with(
            json.dumps({
                'sha': 'mocked_sha',
                'repo': 'git@github.com:yelp/detect-secrets',
                'plugins': {
                    'HexHighEntropyString': {
                        'hex_limit': 3,
                    },
                    'Base64HighEntropyString': {
                        'base64_limit': 4.5,
                    },
                    'PrivateKeyDetector': {},
                    'BasicAuthDetector': {},
                },
                'crontab': '',
                'baseline_filename': None,
                'exclude_regex': None,
            }, indent=2, sort_keys=True),
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
                expected_input='git pull',
            ),
            SubprocessMock(
                expected_input='git rev-parse HEAD',
                mocked_output='mocked_sha',
            ),
        ]

        with mock_git_calls(*git_calls):
            args = self.parse_args('add {} --root-dir {}'.format(repo, mock_rootdir))
            add_repo(args)

    def test_add_local_repo(self, mock_file_operations):
        # This just needs to exist; no actual operations will be done to this.
        repo = 'examples'

        git_calls = [
            # repo.update
            SubprocessMock(
                expected_input='git rev-parse HEAD',
                mocked_output='mocked_sha',
            ),

            # repo.save (to get self.name)
            SubprocessMock(
                expected_input='git remote get-url origin',
                mocked_output='git@github.com:yelp/detect-secrets',
            ),
        ]

        with mock_git_calls(*git_calls):
            args = self.parse_args(
                'add {} --baseline .secrets.baseline --local'.format(
                    repo,
                )
            )

            add_repo(args)

        mock_file_operations.write.assert_called_with(
            json.dumps({
                'sha': 'mocked_sha',
                'repo': 'examples',
                'plugins': {
                    'HexHighEntropyString': {
                        'hex_limit': 3,
                    },
                    'Base64HighEntropyString': {
                        'base64_limit': 4.5,
                    },
                    'PrivateKeyDetector': {},
                    'BasicAuthDetector': {},
                },
                'crontab': '',
                'baseline_filename': '.secrets.baseline',
                'exclude_regex': None,
            }, indent=2, sort_keys=True)
        )

    def test_add_s3_backend_repo(self, mock_file_operations, mocked_boto):
        args = self.parse_args(
            'add {} '
            '--local '
            '--s3-credentials-file examples/aws_credentials.json '
            '--s3-bucket pail'.format('examples'),
            is_s3=True,
        )

        git_calls = [
            # repo.update
            SubprocessMock(
                expected_input='git rev-parse HEAD',
                mocked_output='mocked_sha',
            ),

            # repo.save (to get self.name)
            SubprocessMock(
                expected_input='git remote get-url origin',
                mocked_output='git@github.com:yelp/detect-secrets',
            ),

            # s3 repo.save
            SubprocessMock(
                expected_input='git remote get-url origin',
                mocked_output='git@github.com:yelp/detect-secrets',
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
