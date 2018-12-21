from __future__ import absolute_import

from contextlib import contextmanager

import mock
import pytest

from detect_secrets_server.repos.base_tracked_repo import OverrideLevel
from detect_secrets_server.repos.s3_tracked_repo import S3LocalTrackedRepo
from detect_secrets_server.repos.s3_tracked_repo import S3TrackedRepo
from testing.factories import metadata_factory


class TestS3TrackedRepo(object):

    def test_load_from_file(self, mock_logic, mock_rootdir):
        with mock_logic() as (client, repo):
            assert repo.s3_config == mock_s3_config()

            filename = '{}.json'.format(
                repo.storage.hash_filename('mocked_repository_name'),
            )
            client.download_file.assert_called_with(
                'pail',
                'prefix/{}'.format(filename),
                '{}/tracked/{}'.format(
                    mock_rootdir,
                    filename,
                ),
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


def mock_s3_config():
    return {
        'prefix': 'prefix',
        'bucket': 'pail',
        'credentials_filename': 'examples/aws_credentials.json',
        'access_key': 'access_key',
        'secret_access_key': 'secret_access_key',
    }


@pytest.fixture
def mock_logic(mocked_boto, mock_rootdir):
    @contextmanager
    def wrapped(is_local=False):
        klass = S3LocalTrackedRepo if is_local else S3TrackedRepo

        with mock.patch(
            'detect_secrets_server.storage.file.open',
            mock.mock_open(
                read_data=metadata_factory(
                    'git@github.com:yelp/detect-secrets',
                    json=True,
                ),
            )
        ), mock.patch(
            'detect_secrets_server.storage.file.os.path.isdir',
            return_value=True,
        ):
            yield (
                mocked_boto,
                klass.load_from_file(
                    'mocked_repository_name',
                    mock_rootdir,
                    mock_s3_config(),
                )
            )

    return wrapped
