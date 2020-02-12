from unittest import mock

import pytest


@pytest.fixture
def mock_file_operations():
    """Mocks out certain calls in BaseTrackedRepo that attempts to
    write to disk.
    """
    mock_open = mock.mock_open()
    with mock.patch(
        'detect_secrets_server.storage.base.os.makedirs',
    ), mock.patch(
        'detect_secrets_server.storage.file.open',
        mock_open,
    ):
        yield mock_open()
