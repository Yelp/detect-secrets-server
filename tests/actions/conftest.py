import mock
import pytest


@pytest.fixture
def mock_file_operations():
    """Mocks out certain calls in BaseTrackedRepo that attempts to
    write to disk.
    """
    mock_open = mock.mock_open()
    with mock.patch(
        'detect_secrets_server.repos.BaseTrackedRepo._initialize_tmp_dir',
    ), mock.patch(
        'detect_secrets_server.repos.base_tracked_repo.codecs.open',
        mock_open,
    ):
        yield mock_open()
