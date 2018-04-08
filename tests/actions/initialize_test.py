from __future__ import absolute_import

import os
from contextlib import contextmanager

import mock
import pytest

from detect_secrets_server.actions.initialize import initialize
from detect_secrets_server.usage import ServerParserBuilder


class TestInitialize(object):

    @staticmethod
    def parse_args(argument_string=''):
        base_argument = (
            '--initialize will_be_mocked '
            '--output-hook examples/standalone_hook.py '
        )

        return ServerParserBuilder().parse_args(
            (base_argument + argument_string).split()
        )

    def test_no_tracked_repos(self):
        with mock_repos_config({}):
            args = self.parse_args()

        assert not initialize(args)

    def test_simple_success(self):
        with mock_repos_config({
            'tracked': [
                self.mock_config_data()
            ]
        }):
            args = self.parse_args()

        with mock_repo_class('BaseTrackedRepo') as repo_class:
            initialize(args)

            repo_class.assert_called_with(
                repo='git@github.com:yelp/detect-secrets',
                sha='afe6f0bced18a7f7d56975e6d0cdb45b95fbb4b1',
                cron='* * 4 * *',
                plugins={
                    'HexHighEntropyString': {
                        'hex_limit': [3],
                    },
                    'Base64HighEntropyString': {
                        'base64_limit': [4.5],
                    },
                    'PrivateKeyDetector': {},
                },
                base_temp_dir=os.path.expanduser('~/.detect-secrets-server'),
                baseline_filename='',
                exclude_regex='',
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
            args = self.parse_args()

        with mock_repo_class(expected_repo_class) as repo_class:
            initialize(args)
            assert repo_class.called

    def test_repo_config_overrides_defaults(self):
        with mock_repos_config({
            'tracked': [
                self.mock_config_data({
                    'plugins': {
                        # This checks that it overrides CLI plugin
                        'HexHighEntropyString': 5,

                        # This checks it overrides default values
                        'Base64HighEntropyString': 2,

                        # This checks for disabling functionality
                        'PrivateKeyDetector': False,
                    },

                    # This checks it overrides CLI (non-plugin)
                    'baseline_file': 'baseline.file',

                    # This checks it overrides default value (non-plugin)
                    'exclude_regex': 'something_here',
                })
            ]
        }):
            args = self.parse_args(
                '--hex-limit 4 '
                '--baseline will_be_overriden'
            )

        with mock_repo_class('BaseTrackedRepo') as repo_class:
            initialize(args)

            repo_class.assert_called_with(
                repo='git@github.com:yelp/detect-secrets',
                sha='afe6f0bced18a7f7d56975e6d0cdb45b95fbb4b1',
                cron='* * 4 * *',
                plugins={
                    'HexHighEntropyString': {
                        'hex_limit': [5],
                    },
                    'Base64HighEntropyString': {
                        'base64_limit': [2],
                    },
                },
                base_temp_dir=os.path.expanduser('~/.detect-secrets-server'),
                baseline_filename='baseline.file',
                exclude_regex='something_here',
            )

    def test_cron_output(self, prevent_repo_write_to_disk):
        with mock_repos_config({
            'tracked': [
                self.mock_config_data(),
                self.mock_config_data({
                    'repo': 'git@github.com:yelp/detect-secrets-server',
                    'cron': '* * 2 * *',
                }),
            ]
        }):
            args = self.parse_args()

        assert initialize(args) == (
            '# detect-secrets scanner\n'
            '* * 4 * *    detect-secrets-server '
            '--scan-repo yelp/detect-secrets '
            '--output-hook examples/standalone_hook.py\n'
            '* * 2 * *    detect-secrets-server '
            '--scan-repo yelp/detect-secrets-server '
            '--output-hook examples/standalone_hook.py'
        )

    @staticmethod
    def mock_config_data(extra_data=None):
        if not extra_data:
            extra_data = {}

        required_args = {
            'repo': 'git@github.com:yelp/detect-secrets',
            'sha': 'afe6f0bced18a7f7d56975e6d0cdb45b95fbb4b1',
            'cron': '* * 4 * *',
        }

        required_args.update(extra_data)

        return required_args


@contextmanager
def mock_repos_config(data):
    """Unfortunately, mocking this means that we can't test more than
    one config file at a time. However, all consolidation tests with
    --config-file should have been done in usage_test, so we should
    be OK.
    """
    with mock.patch(
            'detect_secrets_server.usage.is_config_file',
            return_value=data,
    ):
        yield


@contextmanager
def mock_repo_class(classname):
    """
    :type classname: str
    """
    with mock.patch(
            'detect_secrets_server.repos.{}'.format(classname),
    ) as repo_class:
        yield repo_class


@pytest.fixture
def prevent_repo_write_to_disk():
    """Mocks out certain calls in BaseTrackedRepo that attempts to
    write to disk.
    """
    with mock.patch(
        'detect_secrets_server.repos.BaseTrackedRepo._initialize_tmp_dir',
    ), mock.patch(
        'detect_secrets_server.repos.base_tracked_repo.codecs.open'
    ):
        yield
