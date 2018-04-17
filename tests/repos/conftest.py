import pytest


@pytest.fixture
def mock_tracked_repo_data():
    return {
        'repo': 'git@github.com:yelp/detect-secrets',
        'sha': 'sha256-hash',
        'cron': '1 2 3 4 5',
        'plugins': {
            'HexHighEntropyString': 2.5,
        },
        'baseline_filename': 'foobar',
        'exclude_regex': '',
    }
