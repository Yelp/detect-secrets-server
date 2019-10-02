from __future__ import absolute_import

import os
import tempfile
import textwrap
from contextlib import contextmanager

import mock
import pytest

from detect_secrets_server.actions.install import install_mapper
from detect_secrets_server.core.usage.parser import ServerParserBuilder
from testing.factories import metadata_factory


class TestInstallCron(object):

    @staticmethod
    def parse_args(rootdir, argument_string=''):
        with mock.patch(
            'detect_secrets_server.core.usage.s3.should_enable_s3_options',
            return_value=False,
        ):
            return ServerParserBuilder().parse_args(
                'install cron --root-dir {} {}'.format(
                    rootdir,
                    argument_string,
                ).split()
            )


    def test_writes_crontab(self, mock_crontab, mock_rootdir, mock_metadata):
        args = self.parse_args(mock_rootdir)
        with mock_metadata(
            remote_files=(
                metadata_factory(
                    repo='git@github.com:yelp/detect-secrets',
                    json=True,
                ),
            ),
            local_files=(
                metadata_factory(
                    repo='examples',
                    json=True,
                ),
            )
        ):
            install_mapper(args)

        assert mock_crontab.content == textwrap.dedent("""
            0 0 * * *    detect-secrets-server scan git@github.com:yelp/detect-secrets --root-dir {}
            0 0 * * *    detect-secrets-server scan examples --local --root-dir {}
        """).format(mock_rootdir, mock_rootdir)[1:-1]
        mock_crontab.write_to_user.assert_called_with(user=True)

    def test_crontab_writes_with_output_hook(
        self,
        mock_crontab,
        mock_rootdir,
        mock_metadata,
    ):
        args = self.parse_args(
            mock_rootdir,
            '--output-hook examples/standalone_hook.py'
        )

        with mock_metadata(
            remote_files=(
                metadata_factory(
                    repo='git@github.com:yelp/detect-secrets',
                    crontab='1 2 3 4 5',
                    json=True,
                ),
            ),
        ):
            install_mapper(args)

        assert mock_crontab.content == (
            '1 2 3 4 5    detect-secrets-server scan git@github.com:yelp/detect-secrets'
            ' --root-dir {}'
            ' --output-hook examples/standalone_hook.py'.format(mock_rootdir)
        )
        mock_crontab.write_to_user.assert_called_with(user=True)

    def test_does_not_override_existing_crontab(
        self,
        mock_crontab,
        mock_rootdir,
        mock_metadata,
    ):
        mock_crontab.old_content = textwrap.dedent("""
            * * * * *    detect-secrets-server scan old_config_will_be_deleted --local
            * * * * *    some_content_here
        """)[1:]

        args = self.parse_args(mock_rootdir)
        with mock_metadata(
            local_files=(
                metadata_factory(
                    repo='examples',
                    crontab='1 2 3 4 5',
                    json=True,
                ),
            ),
        ):
            install_mapper(args)

        assert mock_crontab.content == textwrap.dedent("""
            * * * * *    some_content_here

            1 2 3 4 5    detect-secrets-server scan examples --local --root-dir {}
        """).format(mock_rootdir)[1:-1]


@pytest.fixture
def mock_crontab():
    output = mock.Mock()

    def mock_constructor(user, tab='', *args, **kwargs):
        output.content = tab

        return output

    def writer(filename):
        with open(filename, 'w') as f:
            f.write(output.old_content)
    output.write = writer
    output.old_content = ''

    with mock.patch(
        'detect_secrets_server.actions.install.CronTab',
        mock_constructor,
    ):
        yield output


@pytest.fixture
def mock_metadata(mock_rootdir):
    def _write_content(content, is_local=False):
        directory = os.path.join(mock_rootdir, 'tracked')
        if is_local:
            directory = os.path.join(directory, 'local')

        file = tempfile.NamedTemporaryFile(
            dir=directory,
            suffix='.json',
        )
        file.write(content.encode())

        # This makes it so that we can immediately read from it.
        file.seek(0)

        return file

    @contextmanager
    def wrapped(remote_files=None, local_files=None):
        """
        :type remote_files: list(str)
        :param remote_files: list of JSON encoded metadata_factory, for remote repos
        :type local_files: list(str)
        :param local_files: list of JSON encoded metadata_factory, for local repos
        """
        if not remote_files:
            remote_files = []
        if not local_files:
            local_files = []

        for path in (
            os.path.join(mock_rootdir, 'tracked'),
            os.path.join(mock_rootdir, 'tracked/local'),
        ):
            os.mkdir(path)

        temp_files = []
        for content in remote_files:
            temp_files.append(_write_content(content))

        for content in local_files:
            temp_files.append(_write_content(content, is_local=True))

        try:
            yield
        finally:
            for file in temp_files:
                file.close()

    return wrapped
