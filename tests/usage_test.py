from __future__ import absolute_import

from contextlib import contextmanager

import mock
import pytest

from detect_secrets_server.hooks.external import ExternalHook
from detect_secrets_server.hooks.pysensu_yelp import PySensuYelpHook
from detect_secrets_server.usage import ServerParserBuilder


class OptionsTest(object):

    @staticmethod
    def parse_args(argument_string=''):
        return ServerParserBuilder().parse_args(argument_string.split())


@pytest.fixture
def mock_config_file():
    @contextmanager
    def wrapped(config_dict):
        with mock.patch(
                'detect_secrets_server.usage.is_config_file',
                return_value=config_dict,
        ):
            yield

    return wrapped


class TestActionOptions(OptionsTest):

    def test_simultaneous_actions_blocked(self):
        with pytest.raises(SystemExit):
            self.parse_args(
                '--initialize --scan-repo yelp/detect-secrets',
            )

    def test_still_succeed_if_no_action(self):
        self.parse_args('-v')

    @pytest.mark.parametrize(
        'command,will_raise_error',
        [
            (
                '--add-repo git@github.com:yelp/detect-secrets',
                False,
            ),
            (
                '--add-repo https://github.com/Yelp/detect-secrets.git',
                False,
            ),

            # If local, the git url will fail because it's not a folder
            (
                '--add-repo git@github.com:yelp/detect-secrets -L',
                True,
            ),

            # scan-repo does not need a git url
            (
                '--scan-repo yelp/detect-secrets '
                '--output-hook examples/standalone_hook.py',
                False,
            ),

            # Doesn't matter where the repo is: the path just needs to exist
            (
                '--add-repo examples -L',
                False,
            ),
            (
                '--scan-repo examples -L --output-hook examples/standalone_hook.py',
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


class TestInitializeOptions(OptionsTest):

    @pytest.mark.parametrize(
        'config,command,assertion',
        [
            (
                {
                    'plugins': {
                        'Base64HighEntropyString': 4.5,
                    },
                },
                '--base64-limit 4',
                lambda x: x.plugins['Base64HighEntropyString'] == {
                    'base64_limit': [4.0],
                },
            ),

            # Disabled plugin option is still a command line argument
            (
                {
                    'plugins': {
                        'Base64HighEntropyString': 4.5,
                    },
                },
                '--no-base64-string-scan',
                lambda x: 'Base64HighEntropyString' not in x,
            ),

            (
                {
                    'baseline': 'this/will/not/be/replaced',
                },
                '--baseline .secrets.baseline',
                lambda x: x.baseline == ['.secrets.baseline'],
            ),

            (
                {
                    'base_temp_dir': 'this/will/not/be/replaced',
                },
                '--base-temp-dir /some/path/here',
                lambda x: x.base_temp_dir == ['/some/path/here'],
            ),
        ],
    )
    def test_config_file_does_not_override_command_line_args(
            self,
            mock_config_file,
            config,
            command,
            assertion
    ):
        with mock_config_file({
            'default': config,
        }):
            args = self.parse_args(
                '--config-file will_be_mocked {}'.format(command)
            )

        assert assertion(args)

    @pytest.mark.parametrize(
        'config,assertion',
        [
            (
                {
                    'plugins': {
                        'HexHighEntropyString': 2,
                    },
                },
                lambda x: x.plugins['HexHighEntropyString'] == {
                    'hex_limit': [2],
                },
            ),
            (
                {
                    'base_temp_dir': '/replaced/path/here',
                },
                lambda x: x.base_temp_dir == ['/replaced/path/here'],
            ),
            (
                {
                    'baseline': 'baseline.file',
                },
                lambda x: x.baseline == ['baseline.file'],
            ),
            (
                {
                    'exclude_regex': 'blah',
                },
                lambda x: x.exclude_regex == ['blah'],
            ),
        ],
    )
    def test_config_file_overrides_default_value(
            self,
            mock_config_file,
            config,
            assertion
    ):
        with mock_config_file({
            'default': config,
        }):
            args = self.parse_args(
                '--config-file will_be_mocked',
            )

        assert assertion(args)

    def test_config_file_disables_when_appropriate(
            self,
            mock_config_file
    ):
        with mock_config_file(self.mock_config_plugins(
            {
                'PrivateKeyDetector': False,
            }
        )):
            args = self.parse_args(
                '--config-file will_be_mocked',
            )

        assert 'PrivateKeyDetector' not in args

    def test_config_file_unknown_plugin_does_nothing(
            self,
            mock_config_file
    ):
        with mock_config_file(self.mock_config_plugins(
            {
                'blah': 4.5
            }
        )):
            with pytest.raises(KeyError):
                self.parse_args(
                    '--config-file will_be_mocked',
                )

    def test_default_values(self):
        with mock.patch(
                'detect_secrets_server.usage.os.path.expanduser',
        ) as mock_expanduser:
            args = self.parse_args()

            mock_expanduser.assert_called_with('~/.detect-secrets-server')

        assert args.exclude_regex == ['']

    @staticmethod
    def mock_config_plugins(plugins):
        return {
            'default': {
                'plugins': plugins,
            }
        }


class TestOutputOptions(OptionsTest):

    @pytest.mark.parametrize(
        'hook_input',
        [
            # No such hook
            'asdf',

            # config file required
            'pysensu',

            # no such file
            'test_data/invalid_file',
        ]
    )
    def test_invalid_output_hook(self, hook_input):
        with pytest.raises(SystemExit):
            self.parse_args('--output-hook {}'.format(hook_input))

    @pytest.mark.parametrize(
        'hook_input,instance_type',
        [
            (
                # For testing purposes, the exact config does not
                # matter; it just needs to be yaml loadable.
                'pysensu --output-config examples/repos.yaml',
                PySensuYelpHook,
            ),
            (
                'setup.py',
                ExternalHook,
            ),
        ]
    )
    def test_valid_output_hook(self, hook_input, instance_type):
        args = self.parse_args('--output-hook {}'.format(hook_input))
        assert isinstance(args.output_hook, instance_type)

        with pytest.raises(AttributeError):
            getattr(args, 'output_config')

    @pytest.mark.parametrize(
        'action_flag',
        [
            '--initialize examples/repos.yaml',
            '--scan-repo does_not_matter',
        ]
    )
    def test_actions_requires_output_hook(self, action_flag):
        with pytest.raises(SystemExit):
            self.parse_args(action_flag)

        args = self.parse_args('{} --output-hook setup.py'.format(action_flag))
        assert args.output_hook_command == '--output-hook setup.py'
