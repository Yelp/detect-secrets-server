from __future__ import absolute_import

import argparse
import os
from collections import namedtuple
from importlib import import_module

from detect_secrets.core.usage import ParserBuilder

from detect_secrets_server.hooks.external import ExternalHook


class ServerParserBuilder(ParserBuilder):
    """Arguments, for the server component"""

    def __init__(self):
        super(ServerParserBuilder, self).__init__()
        self.output_parser = OutputOptions(self.parser)

        self._add_server_arguments()

    def parse_args(self, argv):
        output = super(ServerParserBuilder, self).parse_args(argv)

        try:
            self.output_parser.consolidate_args(output)
        except argparse.ArgumentTypeError as e:
            self.parser.error(e)

        return output

    def _add_server_arguments(self):
        self._add_initialize_server_argument()\
            ._add_scan_repo_argument()\
            ._add_config_file_argument()\
            ._add_add_repo_argument()\
            ._add_local_repo_flag()\
            ._add_s3_config_file_argument()\
            ._add_set_baseline_argument()

        self.output_parser.add_arguments()

    def _add_initialize_server_argument(self):
        self.parser.add_argument(
            '--initialize',
            nargs='?',
            const='repos.yaml',
            help='Initializes tracked repositories based on a supplied repos.yaml.',
            metavar='CUSTOM_REPO_CONFIG_FILE',
        )

        return self

    def _add_scan_repo_argument(self):
        self.parser.add_argument(
            '--scan-repo',
            nargs=1,
            help='Specify the name of the repo (or path, if local) to scan.',
            metavar='REPO_TO_SCAN',
        )

        return self

    def _add_config_file_argument(self):
        self.parser.add_argument(
            '--config-file',
            nargs=1,
            help='Path to a config.yaml which will be used to initialize defaults and plugins.',
        )

        return self

    def _add_add_repo_argument(self):
        self.parser.add_argument(
            '--add-repo',
            nargs=1,
            help=(
                'Enables the addition of individual tracked git repos, without including it in the config file. '
                'Takes in a git URL (or path to repo, if local) as an argument. '
                'Newly tracked repos will store HEAD as the last scanned commit sha. '
                'Also uses config file specified by `--config-file` to initialize default plugins and other settings.'
            ),
            metavar='REPO_TO_ADD'
        )

        return self

    def _add_local_repo_flag(self):
        self.parser.add_argument(
            '-L',
            '--local',
            action='store_true',
            help=(
                'Allows scanner to be pointed to locally stored repos (instead of git cloning). '
                'Use with --scan-repo or --add-repo.'
            ),
        )

        return self

    def _add_s3_config_file_argument(self):
        self.parser.add_argument(
            '--s3-config-file',
            nargs=1,
            help='Specify keys for storing files on Amazon S3.',
            metavar='S3_CONFIG_FILE',
        )

        return self


class HookDescriptor(namedtuple(
    'HookDescriptor',
    [
        # The value that users can input, to refer to this hook.
        'display_name',

        # module name of plugin, used for initialization
        'module_name',

        'class_name',

        # A HookDescriptor config enum
        'config_setting',
    ]
)):
    CONFIG_NOT_SUPPORTED = 0
    CONFIG_OPTIONAL = 1
    CONFIG_REQUIRED = 2

    def __new__(cls, config_setting=None, **kwargs):
        if config_setting is None:
            config_setting = cls.CONFIG_NOT_SUPPORTED

        return super(HookDescriptor, cls).__new__(
            cls,
            config_setting=config_setting,
            **kwargs
        )


class OutputOptions(object):

    all_hooks = [
        HookDescriptor(
            display_name='pysensu',
            module_name='detect_secrets_server.hooks.pysensu_yelp',
            class_name='PySensuYelpHook',
            config_setting=HookDescriptor.CONFIG_REQUIRED,
        ),
    ]

    def __init__(self, parser):
        self.parser = parser.add_argument_group(
            title='output',
            description=(
                'Configure output method, for alerting upon secrets found in '
                'tracked repository.'
            ),
        )

    def add_arguments(self):
        self.parser.add_argument(
            '--output-hook',
            type=self._is_valid_hook,
            help=(
                'Either one of the pre-registered hooks ({}) '
                'or a path to a valid executable file.'.format(
                    ', '.join(
                        map(
                            lambda x: x.display_name,
                            self.all_hooks,
                        )
                    )
                )
            ),
            metavar='HOOK',
        )

        self.parser.add_argument(
            '--output-config',
            type=is_valid_file,
            help=(
                'Configuration file to initialize output hook, if required.'
            ),
            metavar='CONFIG_FILENAME',
        )

    def consolidate_args(self, args):
        if (args.initialize or args.scan_repo) and not args.output_hook:
            raise argparse.ArgumentTypeError(
                'Specifying an --output-hook is required, when initializing '
                'or scanning your tracked repositories.'
            )

        if args.output_hook:
            args.output_hook, args.output_hook_command = \
                self._initialize_output_hook_and_raw_command(args)
            delattr(args, 'output_config')

        return args

    def _is_valid_hook(self, hook):
        """
        A valid hook is either one of the pre-defined hooks, or a filename
        to an arbitrary executable script (for further customization).
        """
        for registered_hook in self.all_hooks:
            if hook == registered_hook.display_name:
                return hook

        is_valid_file(
            hook,
            [
                '\noutput-hook must be one of the following values:\n' +
                '\n'.join(
                    map(
                        lambda x: '  - ' + x.display_name,
                        self.all_hooks,
                    )
                ) +
                '\nor a valid executable filename.\n' +
                '"{}" does not qualify.'.format(hook),
            ],
        )
        return hook

    def _initialize_output_hook_and_raw_command(self, args):
        hook_found = None
        command = '--output-hook {}'.format(args.output_hook)

        for hook in self.all_hooks:
            if args.output_hook == hook.display_name:
                hook_found = hook
                break

        if not hook_found:
            return ExternalHook(args.output_hook), command

        if hook_found.config_setting == HookDescriptor.CONFIG_REQUIRED and \
                not args.output_config:
            # We want to display this error, as if it was during argument validation.
            raise argparse.ArgumentTypeError(
                '{} hook requires a config file. '
                'Pass one in through --output-config.'.format(
                    hook_found.display_name,
                )
            )

        # These values are not user injectable, so it should be ok.
        module = import_module(hook_found.module_name)
        hook_class = getattr(module, hook_found.class_name)

        if hook_found.config_setting == HookDescriptor.CONFIG_NOT_SUPPORTED:
            return hook_class(), command

        command += ' --output-config {}'.format(args.output_config)
        with open(args.output_config) as f:
            return hook_class(f.read()), command


def is_valid_file(path, error_msg=None):
    if not os.path.exists(path):
        if not error_msg:
            error_msg = 'File does not exist: %s' % path

        raise argparse.ArgumentTypeError(error_msg)

    return path


def is_config_file(path):
    """
    Custom type to enforce input is valid filepath, and if valid,
    extract file contents.
    """
    is_valid_file(path)

    with open(path) as f:
        return f.read()
