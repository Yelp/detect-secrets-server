from __future__ import absolute_import

import json
import os
from contextlib import contextmanager

import mock
import pytest

from detect_secrets_server.repos.base_tracked_repo import OverrideLevel
from detect_secrets_server.repos.s3_tracked_repo import S3LocalTrackedRepo
from detect_secrets_server.repos.s3_tracked_repo import S3TrackedRepo
from tests.util.mock_util import mock_git_calls
from tests.util.mock_util import SubprocessMock


class TestS3TrackedRepo(object):

    def test_load_from_file(self, mock_logic):
        with mock_logic() as (client, repo):
            assert repo.credentials_filename == 'examples/aws_credentials.json'
            assert repo.bucket_name == 'pail'
            assert repo.prefix == 'prefix'

            filename = '{}.json'.format(
                repo.storage.hash_filename('mocked_repository_name'),
            )
            client.download_file.assert_called_with(
                'pail',
                'prefix/{}'.format(filename),
                os.path.expanduser(
                    '~/.detect-secrets-server/tracked/{}'.format(filename),
                )
            )

    def test_cron(self, mock_logic):
        with mock_logic() as (client, repo):
            assert repo.cron() == (
                '1 2 3 4 5    detect-secrets-server '
                '--scan-repo yelp/detect-secrets '
                '--s3-credentials-file examples/aws_credentials.json '
                '--s3-bucket pail '
                '--s3-prefix prefix'
            )

    @pytest.mark.parametrize(
        'is_file_uploaded,override_level,should_upload',
        [
            # If not uploaded, always upload despite OverrideLevel.
            (False, OverrideLevel.NEVER, True,),
            (False, OverrideLevel.ASK_USER, True,),
            (False, OverrideLevel.ALWAYS, True,),

            # Upload if OverrideLevel != NEVER
            (True, OverrideLevel.ALWAYS, True,),
            (True, OverrideLevel.NEVER, False,),
        ]
    )
    def test_save(
            self,
            mock_logic,
            is_file_uploaded,
            override_level,
            should_upload
    ):
        with mock_logic() as (client, repo):
            filename = 'prefix/{}.json'.format(
                repo.storage.hash_filename('yelp/detect-secrets')
            )

            mock_list_objects_return_value = {}
            if is_file_uploaded:
                mock_list_objects_return_value = {
                    'Contents': [
                        {
                            'Key': filename,
                            'Size': 1,
                        },
                    ],
                }

            client.list_objects_v2.return_value = \
                mock_list_objects_return_value

            repo.save(override_level)

            client.list_objects_v2.assert_called_with(
                Bucket='pail',
                Prefix=filename,
            )
            assert client.upload_file.called is should_upload


class TestS3LocalTrackedRepo(object):

    def test_cron(self, mock_logic):
        with mock_logic(is_local=True) as (client, repo),\
            mock_git_calls(
                SubprocessMock(
                    expected_input='git remote get-url origin',
                    mocked_output='git@github.com:yelp/detect-secrets',
                ),
        ):
            assert repo.cron() == (
                '1 2 3 4 5    detect-secrets-server '
                '--scan-repo yelp/detect-secrets '
                '--local '
                '--s3-credentials-file examples/aws_credentials.json '
                '--s3-bucket pail '
                '--s3-prefix prefix'
            )


@pytest.fixture
def mock_logic(mocked_boto, mock_tracked_repo_data):
    @contextmanager
    def wrapped(is_local=False):
        klass = S3LocalTrackedRepo if is_local else S3TrackedRepo

        with mock.patch(
            'detect_secrets_server.storage.file.open',
            mock.mock_open(read_data=json.dumps(
                mock_tracked_repo_data,
            )),
        ), mock.patch(
            'detect_secrets_server.storage.file.os.path.isdir',
            return_value=True,
        ):
            yield (
                mocked_boto,
                klass.load_from_file(
                    'mocked_repository_name',
                    os.path.expanduser('~/.detect-secrets-server'),
                    'examples/aws_credentials.json',
                    'pail',
                    'prefix',
                )
            )

    return wrapped


@pytest.fixture
def mocked_boto():
    with mock.patch(
        'detect_secrets_server.storage.s3.boto3.client',
        return_value=mock.Mock(),
    ) as mock_client:
        yield mock_client()
