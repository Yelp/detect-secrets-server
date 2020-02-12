import argparse
import textwrap
from importlib import import_module

from .hooks import ALL_HOOKS
from .hooks import HookDescriptor
from .validators import is_valid_file
from detect_secrets_server.hooks.external import ExternalHook
from detect_secrets_server.hooks.stdout import StdoutHook


class OutputOptions(object):

    def __init__(self, parser):
        self.parser = parser.add_argument_group(
            title='output settings',
            description=(
                'Configure output method, for alerting upon secrets found '
                'in the tracked repositories.'
            ),
        )

    def add_arguments(self):
        self.parser.add_argument(
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

        self.parser.add_argument(
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

        return StdoutHook(), ''

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
    try:
        module = import_module(hook_found.module_name)
        hook_class = getattr(module, hook_found.class_name)
    except ImportError as e:
        raise argparse.ArgumentTypeError(str(e))

    if hook_found.config_setting == HookDescriptor.CONFIG_NOT_SUPPORTED:
        return hook_class(), command

    command += ' --output-config {}'.format(config_filename)
    with open(config_filename) as f:
        return hook_class(f.read()), command
