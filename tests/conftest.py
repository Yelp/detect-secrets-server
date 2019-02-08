import os
import shutil
import tempfile

import mock
import pytest


@pytest.fixture
def mock_rootdir():
    # We create a temp directory in the current repo, because it will be
    # platform-independent.
    tempdir = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            '../tmp'
        )
    )
    if not os.path.isdir(tempdir):  # pragma: no cover
        os.mkdir(tempdir)

    pathname = tempfile.mkdtemp(dir=tempdir)
    try:
        yield pathname
    finally:
        shutil.rmtree(pathname)


@pytest.fixture
def mocked_boto():
    mock_client = mock.Mock()
    with mock.patch(
        'detect_secrets_server.storage.s3.S3Storage._get_boto3',
        return_value=mock_client,
    ), mock.patch(
        'detect_secrets_server.core.usage.common.storage.should_enable_s3_options',
        return_value=True,
    ), mock.patch(
        'detect_secrets_server.core.usage.s3.should_enable_s3_options',
        return_value=True,
    ):
        yield mock_client.client()
