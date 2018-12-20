import pytest


@pytest.fixture
def mock_tracked_repo_data():
    return {
        'repo': 'git@github.com:yelp/detect-secrets',
        'sha': 'sha256-hash',
        'crontab': '1 2 3 4 5',
        'plugins': {
            'HexHighEntropyString': {
                'hex_limit': 3.5,
            },
        },
        'baseline_filename': 'foobar',
        'exclude_regex': '',
    }
