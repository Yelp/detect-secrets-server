import subprocess
from contextlib import contextmanager
from unittest import mock

import pytest

from detect_secrets_server.storage.base import BaseStorage
from detect_secrets_server.storage.base import get_filepath_safe
from detect_secrets_server.storage.base import LocalGitRepository
from testing.mocks import mock_git_calls
from testing.mocks import SubprocessMock


class TestBaseStorage(object):

    def test_setup_creates_directories(self, mock_rootdir, base_storage):
        with assert_directories_created([
            mock_rootdir,
            mock_rootdir + '/repos'
        ]):
            base_storage.setup('git@github.com:yelp/detect-secrets')

    @pytest.mark.parametrize(
        'repo,name',
        [
            (
                'git@github.com:yelp/detect-secrets',
                'yelp/detect-secrets',
            ),

            # Ends with .git
            (
                'git@github.com:yelp/detect-secrets.git',
                'yelp/detect-secrets',
            ),

            # Not git@ prefixed
            (
                'https://github.com/yelp/detect-secrets',
                'yelp/detect-secrets',
            ),
            (
                'https://example.com/yelp/detect-secrets',
                'yelp/detect-secrets',
            ),
            (
                'https://example.com/yelp/detect-secrets.git',
                'yelp/detect-secrets',
            ),

            # Throw a PORT number in for good measure
            (
                'https://example.com:23456/yelp/detect-secrets',
                'yelp/detect-secrets',
            ),
        ],
    )
    def test_repository_name(self, repo, name, base_storage):
        with assert_directories_created():
            assert base_storage.setup(repo).repository_name == name

    def test_baseline_file_does_not_exist(self, base_storage):
        """This also conveniently tests our _git function"""
        with assert_directories_created():
            repo = base_storage.setup('git@github.com:yelp/detect-secrets')

        with pytest.raises(subprocess.CalledProcessError):
            repo.get_baseline_file('does_not_exist')

    def test_clone_repo_if_exists(self, base_storage, mock_rootdir):
        with assert_directories_created():
            repo = base_storage.setup('git@github.com:yelp/detect-secrets')

        with mock_git_calls(
            self.construct_subprocess_mock_git_clone(
                repo,
                b'fatal: destination path \'blah\' already exists',
                mock_rootdir,
            ),
        ):
            repo.clone()

    def test_clone_repo_something_else_went_wrong(self, mock_rootdir, base_storage):
        with assert_directories_created():
            repo = base_storage.setup('git@github.com:yelp/detect-secrets')

        with mock_git_calls(
            self.construct_subprocess_mock_git_clone(
                repo,
                b'Some other error message, not expected',
                mock_rootdir,
            )
        ), pytest.raises(
            subprocess.CalledProcessError
        ):
            repo.clone()

    @staticmethod
    def construct_subprocess_mock_git_clone(repo, mocked_output, mock_rootdir):
        return SubprocessMock(
            expected_input=(
                'git clone git@github.com:yelp/detect-secrets {} --bare'.format(
                    '{}/repos/{}'.format(
                        mock_rootdir,
                        repo.hash_filename('yelp/detect-secrets'),
                    ),
                )
            ),
            mocked_output=mocked_output,
            should_throw_exception=True,
        )


class TestLocalGitRepository(object):

    @pytest.mark.parametrize(
        'repo,name',
        [
            (
                '/file/to/yelp/detect-secrets',
                'yelp/detect-secrets',
            ),
            (
                '/file/to/yelp/detect-secrets/.git',
                'yelp/detect-secrets',
            ),
        ]
    )
    def test_name(self, repo, name, local_storage):
        """OK, I admit this is kinda a lame test case, because technically
        everything is mocked out. However, it's needed for coverage, and
        it *does* test things (kinda).
        """
        with mock_git_calls(
            SubprocessMock(
                expected_input='git remote get-url origin',
                mocked_output='git@github.com:yelp/detect-secrets',
            ),
        ), assert_directories_created():
            assert local_storage.setup(repo).repository_name == name

    def test_clone(self, local_storage):
        # We're asserting that nothing is run in this case.
        with mock_git_calls(), assert_directories_created():
            local_storage.setup('git@github.com:yelp/detect-secrets')\
                .clone()


class TestGetFilepathSafe(object):

    @pytest.mark.parametrize(
        'prefix,filename,expected',
        [
            ('/path/to', 'file', '/path/to/file',),
            ('/path/to', '../to/file', '/path/to/file',),
            ('/path/to/../to', 'file', '/path/to/file',),
        ]
    )
    def test_success(self, prefix, filename, expected):
        assert get_filepath_safe(prefix, filename) == expected

    def test_failure(self):
        with pytest.raises(ValueError):
            get_filepath_safe('/path/to', '../../etc/pwd')


@contextmanager
def assert_directories_created(directories_created=None):
    """
    :type directories_created: list
    """
    with mock.patch(
        'detect_secrets_server.storage.base.os.makedirs'
    ) as makedirs, mock.patch(
        'detect_secrets_server.storage.base.os.path.isdir',
        return_value=False,
    ):
        yield

        if directories_created:
            makedirs.assert_has_calls(map(
                lambda x: mock.call(x),
                directories_created,
            ))
        else:
            assert makedirs.called


@pytest.fixture
def base_storage(mock_rootdir):
    return get_mocked_class(BaseStorage)(mock_rootdir)


@pytest.fixture
def local_storage(mock_rootdir):
    return get_mocked_class(LocalGitRepository)(mock_rootdir)


def get_mocked_class(class_object):
    class MockStorage(class_object):  # pragma: no cover
        def get(self, key):
            pass

        def put(self, key, value):
            pass

        def get_tracked_repositories(self):
            return ()

    return MockStorage
