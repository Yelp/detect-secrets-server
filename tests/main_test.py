from __future__ import absolute_import

import mock
import pytest

from detect_secrets_server.__main__ import main
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
