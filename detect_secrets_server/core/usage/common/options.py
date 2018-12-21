import argparse
import os
import textwrap
from abc import ABCMeta
from importlib import import_module

from detect_secrets.core.usage import PluginOptions

from .. import s3
from .hooks import ALL_HOOKS
from .hooks import HookDescriptor
from .validators import is_valid_file
from detect_secrets_server.hooks.external import ExternalHook


class CommonOptions(object):
    """There are some common flags between AddOptions and ScanOptions, that
    we don't want to display in the main help section.

    This contains those flags.
    """
    __metaclass__ = ABCMeta

    def __init__(self, subparser, action):
        self.parser = subparser.add_parser(action)
        self._add_common_arguments()
        PluginOptions(self.parser).add_arguments()

    def _add_common_arguments(self):
        self.parser.add_argument(
            '-L',
            '--local',
            action='store_true',
            help=(
                'Indicates that the repo argument is a locally stored '
                'repository (rather than a git URL to be cloned).'
            ),
        )

        self.parser.add_argument(
            '--root-dir',
            type=str,
            nargs=1,
            default=['~/.detect-secrets-server'],
            help=(
                'Specify location to clone git repositories to. This '
                'folder will also hold any metadata tracking files, if '
                'no other persistent storage option is selected. '
                'Default: ~/.detect-secrets-server'
            ),
        )

        self._add_output_arguments()

        s3.S3Options(self.parser).add_arguments()

    def _add_output_arguments(self):
        """
        While this is mainly used for ScanOptions, AddOptions needs it to
        output the cron commands, so that it can be fed into ScanOptions.
        """
        parser = self.parser.add_argument_group(
            title='output settings',
            description=(
                'Configure output method, for alerting upon secrets found '
                'in the tracked repositories.'
            ),
        )

        parser.add_argument(
            '--output-hook',
            type=_is_valid_output_hook,
            help=(
                'Either one of the pre-registered hooks ({}) '
                'or a path to a valid executable file.'.format(
                    ', '.join(
                        map(
                            lambda x: x.display_name,
                            ALL_HOOKS,
                        )
                    )
                )
            ),
            metavar='HOOK',
        )

        parser.add_argument(
            '--output-config',
            type=is_valid_file,
            help=(
                'Configuration file to initialize output hook, if required.'
            ),
            metavar='CONFIG_FILENAME',
        )

        return self

    @staticmethod
    def consolidate_args(args):
        """
        Based on the --output-hook specified, performs validation and
        initializes args.output_hook, args.output_hook_command.
        """
        args.output_hook, args.output_hook_command = \
            _initialize_output_hook_and_raw_command(
                args.output_hook,
                args.output_config,
            )

        args.root_dir = os.path.abspath(
            os.path.expanduser(args.root_dir[0])
        )

        s3.S3Options.consolidate_args(args)


def _initialize_output_hook_and_raw_command(hook_name, config_filename):
    """
    :rtype: tuple(BaseHook, str)
    :returns:
        BaseHook is the the hook instance to interact with
        output_hook_command is how to call the output-hook as CLI args.
    """
    hook_found = None
    command = '--output-hook {}'.format(hook_name)

    for hook in ALL_HOOKS:
        if hook_name == hook.display_name:
            hook_found = hook
            break
    else:
        if hook_name:
            return ExternalHook(hook_name), command

        return None, ''

    if hook_found.config_setting == HookDescriptor.CONFIG_REQUIRED and \
            not config_filename:
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

    command += ' --output-config {}'.format(config_filename)
    with open(config_filename) as f:
        return hook_class(f.read()), command


def _is_valid_output_hook(hook):
    """
    A valid hook is either one of the pre-defined hooks, or a filename
    to an arbitrary executable script (for further customization).
    """
    for registered_hook in ALL_HOOKS:
        if hook == registered_hook.display_name:
            return hook

    is_valid_file(
        hook,
        textwrap.dedent("""
            output-hook must be one of the following values:
            {}
            or a valid executable filename.

            "{}" does not qualify.
        """)[:-1].format(
            '\n'.join(
                map(
                    lambda x: '  - {}'.format(x.display_name),
                    ALL_HOOKS,
                )
            ),
            hook,
        ),
    )

    return hook
