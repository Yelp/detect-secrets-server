from __future__ import absolute_import

import pytest

from testing.base_usage_test import UsageTest


class TestS3Options(UsageTest):

    def parse_args(self, argument_string='', has_boto=True):
        # This test suite uses `scan` to test, because the API is a lot simpler.
        argument_string = '{} {} {}'.format(
            'scan --output-hook examples/standalone_hook.py --storage s3',
            argument_string,
            'examples -L',
        )
        return super(TestS3Options, self).parse_args(
            argument_string,
            has_boto,
        )

    def test_should_fail_to_find_s3_arguments(self):
        with pytest.raises(SystemExit):
            self.parse_args(
                '--s3-credentials-file examples/aws_credentials.json --s3-bucket BUCKET',
                has_boto=False,
            )

    def test_success(self):
        args = self.parse_args(
            (
                '--s3-credentials-file examples/aws_credentials.json '
                '--s3-bucket BUCKET '
                '--s3-prefix p'
            )
        )

        assert not any([
            getattr(args, 's3_bucket', None),
            getattr(args, 's3_prefix', None),
            getattr(args, 's3_credentials_file', None),
        ])
        assert args.s3_config == {
            'prefix': 'p',
            'bucket': 'BUCKET',
            'creds_filename': 'examples/aws_credentials.json',
            'access_key': 'access_key',
            'secret_access_key': 'secret_key',
        }
