from __future__ import absolute_import

import hashlib
import json
import unittest

import mock

from detect_secrets_server.__main__ import main
from detect_secrets_server.__main__ import parse_args
from detect_secrets_server.__main__ import parse_s3_config
from detect_secrets_server.repos.s3_tracked_repo import S3Config
from tests.util.mock_util import mock_subprocess
from tests.util.mock_util import SubprocessMock


class ServerTest(unittest.TestCase):

    def test_parse_s3_config_fail(self):
        # No file supplied
        mock_args = parse_args([])
        assert parse_s3_config(mock_args) is None

        # Bad initialization of S3Config
        m = mock.mock_open(read_data='{}')
        mock_args = parse_args(['--s3-config-file', 'will_be_mocked'])
        with mock.patch('detect_secrets_server.__main__.codecs.open', m):
            assert parse_s3_config(mock_args) is None

    def test_parse_s3_config_success(self):
        mock_args = parse_args(['--s3-config-file', 'will_be_mocked'])
        data = {
            's3_creds_file': 's3_creds_file.json',
            'bucket_name': 'bucket_name',
            'prefix': 'prefix',
        }
        m = mock.mock_open(read_data=json.dumps(data))
        with mock.patch('detect_secrets_server.__main__.codecs.open', m):
            output = parse_s3_config(mock_args)

        assert isinstance(output, S3Config)
        assert output.bucket_name == 'bucket_name'
        assert output.prefix == 'prefix'

    @mock.patch('detect_secrets_server.repos.s3_tracked_repo.S3TrackedRepo.S3')
    @mock.patch('detect_secrets_server.repos.base_tracked_repo.subprocess.check_output')
    def test_main_add_repo_s3(self, mock_subprocess_obj, mock_s3_obj):
        mock_subprocess_obj.side_effect = mock_subprocess((
            # mock out `_get_repo_name`
            SubprocessMock(
                expected_input='git remote get-url origin',
                mocked_output=b'git@github.com:yelp/detect-secrets',
            ),

            # mock out `update`
            SubprocessMock(
                expected_input='git rev-parse HEAD',
                mocked_output=b'new-sha-hash',
            )
        ))

        mock_s3_config = {
            's3_creds_file': 'filename',
            'bucket_name': 'bucketman',
            'prefix': 'mister',
        }

        final_output = mock.mock_open()
        s3_config = mock.mock_open(read_data=json.dumps(mock_s3_config))
        with mock.patch('detect_secrets_server.repos.base_tracked_repo.codecs.open', final_output),\
                mock.patch('detect_secrets_server.__main__.codecs.open', s3_config),\
                mock.patch(
                    'detect_secrets_server.repos.s3_tracked_repo.S3TrackedRepo._initialize_s3_client'
        ):
            assert main([
                '--add-repo',
                'git@github.com:yelp/detect-secrets.git',
                '--s3-config-file',
                'will-be-mocked',
            ]) == 0

        mock_s3_obj.list_objects_v2.assert_called_once_with(
            Bucket='bucketman',
            Prefix='mister/%s.json' % hashlib.sha512(
                'yelp/detect-secrets'.encode('utf-8')
            ).hexdigest(),
        )

        assert mock_s3_obj.upload_file.call_count == 1

    def test_main_no_args(self):
        # Needed for coverage
        assert main([]) == 0
