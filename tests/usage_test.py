from __future__ import absolute_import

import pytest

from detect_secrets_server.usage import ServerParserBuilder
from detect_secrets_server.hooks.external import ExternalHook
from detect_secrets_server.hooks.pysensu_yelp import PySensuYelpHook


class TestOutputOptions(object):

    @staticmethod
    def parse_args(argument_string=''):
        return ServerParserBuilder().parse_args(argument_string.split())

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
                'pysensu --output-config repos.yaml.sample',
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

