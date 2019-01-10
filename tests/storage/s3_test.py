from __future__ import absolute_import

from datetime import datetime

import pytest
from mock import mock

from detect_secrets_server.storage.s3 import S3Storage
from testing.mocks import mock_open


def test_get_does_not_download_if_exists(mock_logic):
    with mock.patch(
        'detect_secrets_server.storage.s3.os.path.exists',
        return_value=True,
    ), mock_open():
        mock_logic.get('filename', force_download=False)

    assert not mock_logic.client.download_file.called


def test_get_tracked_repositories(mock_logic):
    # Honestly, this is just a smoke test, because to get proper testing,
    # you would need to hook this up to an s3 bucket.
    with mock.patch.object(
        mock_logic.client,
        'get_paginator',
    ) as mock_paginator, mock.patch.object(
        mock_logic,
        'get',
    ) as mock_get:
        mock_paginator().paginate.return_value = (
            {
                'Contents': [
                    {
                        'Key': 'prefix/filenameA.json',
                        'LastModified': datetime.now(),
                        'Size': 500,
                    },
                ],
            },
            {
                'Contents': [
                    {
                        'Key': 'prefix/filenameB.json',
                        'LastModified': datetime.now(),
                        'Size': 200,
                    },
                ],
            },

        )
        list(mock_logic.get_tracked_repositories())

        mock_get.assert_has_calls([
            mock.call('filenameA', force_download=False),
            mock.call('filenameB', force_download=False),
        ])


@pytest.fixture
def mock_logic(mocked_boto, mock_rootdir):
    yield S3Storage(
        mock_rootdir,
        {
            'access_key': 'will_be_mocked',
            'secret_access_key': 'will_be_mocked',
            'bucket': 'pail',
            'prefix': 'prefix',
        },
    )
