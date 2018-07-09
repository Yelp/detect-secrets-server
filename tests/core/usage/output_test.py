from __future__ import absolute_import

import pytest

from detect_secrets_server.hooks.external import ExternalHook
from detect_secrets_server.hooks.pysensu_yelp import PySensuYelpHook
from testing.base_usage_test import UsageTest


class TestOutputOptions(UsageTest):

    def parse_args(self, argument_string=''):
        return super(TestOutputOptions, self).parse_args(
            argument_string,
        )

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
            self.parse_args('scan --output-hook {} examples -L'.format(hook_input))

    @pytest.mark.parametrize(
        'hook_input,instance_type',
        [
            (
                # For testing purposes, the exact config does not
                # matter; it just needs to be yaml loadable.
                'pysensu --output-config examples/pysensu.config.yaml',
                PySensuYelpHook,
            ),
            (
                'examples/standalone_hook.py',
                ExternalHook,
            ),
        ]
    )
    def test_valid_output_hook(self, hook_input, instance_type):
        args = self.parse_args('scan --output-hook {} examples -L'.format(hook_input))
        assert isinstance(args.output_hook, instance_type)

    def test_no_hook_provided(self):
        args = self.parse_args('add git@git.github.com:Yelp/detect-secrets')
        assert not args.output_hook
        assert args.output_hook_command == ''
