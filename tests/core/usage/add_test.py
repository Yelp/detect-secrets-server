import mock
import pytest

from testing.base_usage_test import UsageTest


class TestAddOptions(UsageTest):

    @pytest.mark.parametrize(
        'command, will_raise_error',
        [
            (
                'add git@github.com:yelp/detect-secrets',
                False,
            ),
            (
                'add https://github.com/Yelp/detect-secrets.git',
                False,
            ),

            # If local, the git url will fail because it's not a folder
            (
                'add git@github.com:yelp/detect-secrets -L',
                True,
            ),

            # Doesn't matter where the repo is: the path just needs to exist
            (
                'add examples -L ',
                False,
            ),
        ],
    )
    def test_ensure_parameter_is_git_url(self, command, will_raise_error):
        if will_raise_error:
            with pytest.raises(SystemExit):
                self.parse_args(command)
        else:
            self.parse_args(command)

    def test_adhoc_settings(self):
        args = self.parse_args(
            'add examples -L '
            '--baseline .baseline '
            # '--exclude-regex regex '
            '--exclude-files-regex regex '
            '--exclude-lines-regex regex '
            '--root-dir /tmp'
        )

        assert args.baseline == '.baseline'
        # assert args.exclude_regex == 'regex'
        assert args.exclude_files_regex == 'regex'
        assert args.exclude_lines_regex == 'regex'
        assert args.root_dir == '/tmp'

    def test_local_config_does_not_make_sense(self):
        with pytest.raises(SystemExit):
            self.parse_args(
                'add examples/repos.yaml --config --local'
            )

    def test_invalid_config_file(self):
        with pytest.raises(SystemExit), mock.patch(
            'detect_secrets_server.core.usage.add.config_file',
            return_value={'foo': 'bar'},
        ):
            self.parse_args('add will_be_mocked')

    def test_config_file(self):
        args = self.parse_args(
            'add examples/repos.yaml --config '
        )

        assert args.repo[0]['repo'] == \
            'git@github.com:yelp/detect-secrets.git'

    def test_config_file_does_not_override_command_line_args(self):
        args = self.parse_args(
            'add examples/repos.yaml --config'
        )

        # Config file overrides default values
        assert args.repo[0]['plugins']['Base64HighEntropyString']['base64_limit'] == 4

        # Default values are used
        assert args.plugins['PrivateKeyDetector'] == {}
        assert args.repo[0]['plugins']['HexHighEntropyString']['hex_limit'] == 3

        args = self.parse_args(
            'add examples/repos.yaml --config '
            '--no-private-key-scan '
            '--base64-limit 5'
        )

        # CLI options overrides config file
        assert args.repo[0]['plugins']['Base64HighEntropyString']['base64_limit'] == 5
        assert 'PrivateKeyDetector' not in args.plugins

        # Default values still used
        assert args.repo[0]['plugins']['HexHighEntropyString']['hex_limit'] == 3

    def test_config_file_unknown_plugin_does_nothing(self):
        mock_config_file = {
            'tracked': [
                {
                    'repo': 'git@github.com:yelp/detect-secrets',
                    'plugins': {
                        'blah': {
                            'arg_name': 1,
                        },
                    },
                },
            ],
        }
        with mock.patch(
            'detect_secrets_server.core.usage.add.config_file',
            return_value=mock_config_file,
        ):
            args = self.parse_args('add will_be_mocked --config')

        assert 'blah' not in args.repo[0]['plugins']

    @pytest.mark.parametrize(
        'repo',
        (
            {
                'repo': 'non_existent_file',
                'crontab': '* * 4 * *',
                'is_local_repo': True,
            },
            {
                'repo': 'examples',
                'crontab': '* * 4 * *',
            },
        ),
    )
    def test_config_file_unknown_repos_are_discarded(self, repo):
        with mock.patch(
            'detect_secrets_server.core.usage.add.config_file',
            return_value={
                'tracked': [repo],
            },
        ):
            args = self.parse_args('add will_be_mocked --config')

        assert not args.repo
