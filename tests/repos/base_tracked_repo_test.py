from __future__ import absolute_import

import json
import os
from contextlib import contextmanager

import mock
import pytest

from detect_secrets_server.repos.base_tracked_repo import BaseTrackedRepo
from detect_secrets_server.repos.base_tracked_repo import OverrideLevel
from detect_secrets_server.storage.file import FileStorage
from testing.mocks import mock_git_calls
from testing.mocks import SubprocessMock


class TestLoadFromFile(object):

    def test_success(self, mock_logic, mock_tracked_repo_data):
        mock_open = mock.mock_open(read_data=json.dumps(
            mock_tracked_repo_data,
        ))

        repo = mock_logic(mock_open)

        mock_open.assert_called_with(
            os.path.expanduser(
                '~/.detect-secrets-server/tracked/{}.json'.format(
                    FileStorage.hash_filename('will_be_mocked'),
                )
            ),
        )

        assert repo.last_commit_hash == 'sha256-hash'
        assert repo.repo == 'git@github.com:yelp/detect-secrets'
        assert repo.crontab == '1 2 3 4 5'
        assert repo.plugin_config == {
            'HexHighEntropyString': {
                'hex_limit': [2.5],
            },
        }
        assert repo.baseline_filename == 'foobar'
        assert repo.exclude_regex == ''
        assert isinstance(repo.storage, FileStorage)

    def test_no_file_found(self):
        with pytest.raises(IOError):
            BaseTrackedRepo.load_from_file(
                'does_not_exist',
                os.path.expanduser('~/.detect-secrets-server'),
            )


class TestCron(object):

    def test_success(self, mock_logic):
        repo = mock_logic()
        assert repo.cron() == (
            '1 2 3 4 5    detect-secrets-server '
            '--scan-repo yelp/detect-secrets'
        )


class TestScan(object):

    def test_no_baseline(self, mock_logic):
        repo = mock_logic()
        with mock_git_calls(*self.git_calls()):
            secrets = repo.scan()

        assert len(secrets.data['detect_secrets_server/usage.py']) == 1

    def test_unable_to_find_baseline(self, mock_logic):
        calls = self.git_calls()
        calls[-1] = SubprocessMock(
            expected_input='git show HEAD:foobar',
            mocked_output=b'fatal: Path \'foobar\' does not exist',
            should_throw_exception=True,
        )

        repo = mock_logic()
        with mock_git_calls(*calls):
            secrets = repo.scan()

        assert len(secrets.data['detect_secrets_server/usage.py']) == 1

    def test_scan_with_baseline(self, mock_logic):
        baseline = json.dumps({
            'results': {
                'detect_secrets_server/usage.py': [
                    {
                        'type': 'High Entropy String',
                        'hashed_secret': '87acec17cd9dcd20a716cc2cf67417b71c8a7016',
                        'line_number': 0,       # does not matter
                    },
                ],
            },
            'exclude_regex': None,
        })

        calls = self.git_calls()
        calls[-1] = SubprocessMock(
            expected_input='git show HEAD:foobar',
            mocked_output=baseline,
        )

        repo = mock_logic()
        with mock_git_calls(*calls):
            secrets = repo.scan()

        assert len(secrets.data) == 0

    def test_scan_nonexistent_last_saved_hash(self, mock_logic):
        calls = self.git_calls()
        calls[-2] = SubprocessMock(
            expected_input='git diff sha256-hash HEAD -- detect_secrets_server/usage.py',
            mocked_output=b'fatal: the hash is not in git history',
            should_throw_exception=True,
        )
        calls[-1] = SubprocessMock(
            expected_input='git rev-parse HEAD',
        )

        repo = mock_logic()
        with mock_git_calls(*calls):
            secrets = repo.scan()

        assert secrets.data == {}

    def git_calls(self):
        """We need to do a bunch of mocking, because there's a lot of git
        operations. This function handles all that.
        """
        tracked_location = os.path.expanduser(
            '~/.detect-secrets-server/repos/{}'.format(
                FileStorage.hash_filename('yelp/detect-secrets'),
            )
        )

        with open('test_data/sample.diff') as f:
            diff_content = f.read()

        return [
            # clone and pull master
            SubprocessMock(
                expected_input=(
                    'git clone git@github.com:yelp/detect-secrets {} --bare'.format(
                        tracked_location,
                    )
                ),
            ),
            SubprocessMock(
                expected_input='git pull',
            ),

            # get diff (filtering out ignored file extensions)
            SubprocessMock(
                expected_input='git diff sha256-hash HEAD --name-only',
                mocked_output='detect_secrets_server/usage.py',
            ),
            SubprocessMock(
                expected_input='git diff sha256-hash HEAD -- detect_secrets_server/usage.py',
                mocked_output=diff_content,
            ),

            # get baseline file
            SubprocessMock(
                expected_input='git show HEAD:foobar',
                mocked_output=b'',
            ),
        ]


class TestUpdate(object):

    def test_success(self, mock_logic):
        repo = mock_logic()

        with mock_git_calls(
            SubprocessMock(
                expected_input='git rev-parse HEAD',
                mocked_output='new_hash',
            )
        ):
            repo.update()

        assert repo.last_commit_hash == 'new_hash'


class TestSave(object):

    @pytest.mark.parametrize(
        'override_level,is_file,mocked_input',
        [
            # OverrideLevel doesn't matter if no file exists.
            (OverrideLevel.NEVER, False, '',),
            (OverrideLevel.ASK_USER, False, '',),
            (OverrideLevel.ALWAYS, False, '',),

            # Override file, if desired.
            (OverrideLevel.ALWAYS, True, '',),

            # Override file, if user requested.
            (OverrideLevel.ASK_USER, True, 'y',),
        ],
    )
    def test_save_on_conditions(
            self,
            override_level,
            is_file,
            mocked_input,
            mock_logic,
            mock_tracked_repo_data
    ):
        with self.setup_env(mock_logic, is_file, mocked_input) as (repo, mock_open):
            assert repo.save(override_level)

            self.assert_writes_accurately(mock_open, mock_tracked_repo_data)

    @pytest.mark.parametrize(
        'override_level,is_file,mocked_input',
        [
            (OverrideLevel.NEVER, True, '',),
            (OverrideLevel.ASK_USER, True, 'n',),
        ],
    )
    def test_does_not_save_on_conditions(
            self,
            mock_logic,
            override_level,
            is_file,
            mocked_input
    ):
        with self.setup_env(mock_logic, is_file, mocked_input) as (repo, mock_open):
            assert not repo.save(override_level)
            assert not mock_open().write.called

    @contextmanager
    def setup_env(self, mock_logic, is_file, mocked_input):
        repo = mock_logic()
        mock_open = mock.mock_open()

        with mock.patch(
            'detect_secrets_server.repos.base_tracked_repo.os.path.isfile',
            return_value=is_file
        ), mock.patch(
            'detect_secrets_server.storage.file.open',
            mock_open,
        ), mock.patch(
            'detect_secrets_server.repos.base_tracked_repo.input',
            return_value=mocked_input,
        ):
            yield repo, mock_open

    def assert_writes_accurately(self, mock_open, mock_tracked_repo_data):
        mock_open.assert_called_with(
            os.path.expanduser(
                '~/.detect-secrets-server/tracked/{}.json'.format(
                    FileStorage.hash_filename('yelp/detect-secrets'),
                )
            ),
            'w',
        )
        mocked_data = mock_tracked_repo_data
        mocked_data['plugins'].update({
            'Base64HighEntropyString': False,
            'PrivateKeyDetector': False,
        })
        mock_open().write.assert_called_with(
            json.dumps(
                mocked_data,
                indent=2,
                sort_keys=True,
            )
        )


@pytest.fixture
def mock_logic(mock_tracked_repo_data):
    def wrapped(mock_open=None):
        """
        :type mock_open: mock.mock_open
        :param mock_open: allows for customized mock_open,
            so can do assertions outside this function.
        """
        if not mock_open:
            mock_open = mock.mock_open(read_data=json.dumps(
                mock_tracked_repo_data,
            ))

        with mock.patch(
            'detect_secrets_server.storage.file.open',
            mock_open
        ), mock.patch(
            'detect_secrets_server.storage.base.os.makedirs',
        ):
            return BaseTrackedRepo.load_from_file(
                'will_be_mocked',
                os.path.expanduser('~/.detect-secrets-server'),
            )

    return wrapped
