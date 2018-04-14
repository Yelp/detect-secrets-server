from __future__ import absolute_import

import argparse
import os
from collections import namedtuple
from importlib import import_module

import yaml
from detect_secrets.core.usage import ParserBuilder

from detect_secrets_server.hooks.external import ExternalHook
from detect_secrets_server.plugins import PluginsConfigParser


class ServerParserBuilder(ParserBuilder):
    """Arguments, for the server component"""

    def __init__(self):
        super(ServerParserBuilder, self).__init__()
        self.action_parser = ActionOptions(self.parser)
        self.initialize_options_parser = InitializeOptions(self.parser)
        self.output_parser = OutputOptions(self.parser)

        self.s3_parser = S3Options(self.parser)

        self._add_server_arguments()

    def parse_args(self, argv):
        """This does not extend off its parent, because we need to run
        action_parser before plugins_parser.
        """
        output = self.parser.parse_args(argv)
        self.initialize_options_parser.consolidate_args(output)
        self.plugins_parser.consolidate_args(output)

        try:
            self.action_parser.consolidate_args(output)
            self.output_parser.consolidate_args(output)
        except argparse.ArgumentTypeError as e:
            self.parser.error(e)

        self.s3_parser.consolidate_args(output)

        return output

    def _add_server_arguments(self):
        self.action_parser.add_arguments()
        self.initialize_options_parser.add_arguments()
        self.output_parser.add_arguments()

        self.s3_parser.add_arguments()


class ActionOptions(object):

    def __init__(self, parser):
        self.parser = parser.add_argument_group(
            title='actions',
            description=(
                'These are the main actions that are used with this tool. '
                'First, add the repositories that should be tracked with '
                'either `--initialize` or `--add-repo`. Then, you can scan '
                'your tracked repositories with `--scan-repo`.'
            ),
        )

    def add_arguments(self):
        self.parser.add_argument(
            '--initialize',
            nargs='?',
            type=is_config_file,
            const='repos.yaml',
            help='Initializes tracked repositories based on a supplied repos.yaml.',
            metavar='REPO_CONFIG_FILE',
        )

        self.parser.add_argument(
            '--add-repo',
            nargs=1,
            help=(
                'Enables the addition of individual tracked git repos, without '
                'including it in repos.yaml. Takes in a git URL (or path to repo, '
                'if local) as an argument. '
                'Newly tracked repositories will store HEAD as the last scanned '
                'commit sha.'
            ),
            metavar='REPO_TO_ADD',
        )

        self.parser.add_argument(
            '--scan-repo',
            nargs=1,
            help='Specify the name of the repo (or path, if local) to scan.',
            metavar='REPO_TO_SCAN',
        )

        self.parser.add_argument(
            '-L',
            '--local',
            action='store_true',
            help=(
                'Allows scanner to be pointed to locally stored repos (instead '
                'of git cloning). Use with --scan-repo or --add-repo.'
            ),
        )

    @staticmethod
    def consolidate_args(args):
        # Ensure only one action can be taken at one time.
        action = None
        for act in [args.initialize, args.add_repo, args.scan_repo]:
            if not act:
                continue

            if action:
                raise argparse.ArgumentTypeError(
                    'Only one action can be selected at once.'
                )

            try:
                action = act[0]
            except KeyError:
                # initialize loads a config file
                action = act

        # Still succeed, if no action is chosen.
        if not action:
            return

        # There can only be one action at this point.
        if args.add_repo:
            if not args.local:
                is_git_url(action)
            else:
                is_valid_file(action)
        elif args.scan_repo and args.local:
            is_valid_file(action)


class InitializeOptions(object):

    def __init__(self, parser):
        self.parser = parser.add_argument_group(
            title='initialize options',
            description=(
                'Configure settings to initialize the server secret scanner. '
                'These settings are to be used with the `--initialize` flag, '
                'or the `--add-repo` flag.'
            ),
        )

    def add_arguments(self):
        self.parser.add_argument(
            '--baseline',
            type=str,
            nargs=1,
            help=(
                'Specify a default baseline filename to look for, in each '
                'tracked repository.'
            ),
        )

        self.parser.add_argument(
            '--base-temp-dir',
            type=str,
            nargs=1,
            help=(
                'Specify location to clone git repositories to. '
                'Default: ~/.detect-secrets-server'
            ),
        )

        self.parser.add_argument(
            '--exclude-regex',
            type=str,
            nargs=1,
            help=(
                'Filenames that match this regex will be ignored when scanning '
                'for secrets.'
            ),
            metavar='REGEX',
        )

        self.parser.add_argument(
            '--config-file',
            type=is_config_file,
            nargs=1,
            help=(
                'An alternative to specifying all default options through the '
                'command line, this allows you to pass all options through a '
                'yaml file instead. However, this does not take precedence '
                'over command line arguments.'
            ),
        )

    @staticmethod
    def consolidate_args(args):
        """This must be called *before* PluginOptions.consolidate_args.
        config_file supports the following values:
            plugins: dict
                Allows the specification of default plugin settings, for
                all repositories scanned. Keys are plugin classnames, and
                values are their initialization values for those classes.

                If the value is False, it will disable that plugin.
            baseline: str
                See help text for --baseline arg.
            base_temp_dir: str
                See help text for --base-temp-dir.
            exclude_regex: str
                See help text for --exclude-regex.
        """
        if args.config_file:
            data = args.config_file[0]['default']
            if 'plugins' in data:
                InitializeOptions._merge_plugin_settings(args, data['plugins'])

            if 'baseline' in data and not args.baseline:
                args.baseline = [data['baseline']]

            if 'base_temp_dir' in data and not args.base_temp_dir:
                args.base_temp_dir = [os.path.abspath(
                    os.path.expanduser(
                        data['base_temp_dir']
                    )
                )]

            if 'exclude_regex' in data and not args.exclude_regex:
                args.exclude_regex = [data['exclude_regex']]

        # This isn't needed anymore
        delattr(args, 'config_file')

        if not args.base_temp_dir:
            args.base_temp_dir = [os.path.expanduser('~/.detect-secrets-server')]

        if not args.baseline:
            args.baseline = ['']

        if not args.exclude_regex:
            args.exclude_regex = ['']

    @staticmethod
    def _merge_plugin_settings(args, plugins):
        """Converts the plugins listed in the config file to their
        corresponding command line flags, so that plugins_parser can
        work its magic.
        """
        for classname, value in plugins.items():
            arg_names = PluginsConfigParser.class_name_to_arg_names(
                classname,
            )

            # If any of the command line arguments are specified for this
            # plugin, then leave it as that (because of precedence).
            if any(map(
                lambda x: getattr(args, x) if x else None,
                arg_names.values()
            )):
                continue

            if value is None or value is False:
                # Disable plugin
                setattr(args, arg_names[True], True)
            else:
                # Some arguments don't have command line flags, so just
                # skip this case.
                if not arg_names[False]:
                    continue

                if not isinstance(value, list):
                    value = [value]

                # Only update if didn't specify on command line
                setattr(args, arg_names[False], value)


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

            # This is not needed anymore
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


class S3Options(object):

    def __init__(self, parser):
        self.parser = parser.add_argument_group(
            title='s3 backend options',
            description=(
                'TODO'
            ),
        )

    def add_arguments(self):
        self.parser.add_argument(
            '--s3-config-file',
            nargs=1,
            type=is_config_file,
            help='Specify keys for storing files on Amazon S3.',
            metavar='S3_CONFIG_FILE',
        )

    @staticmethod
    def consolidate_args(args):
        pass


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
        return yaml.safe_load(f.read())


def is_git_url(url):
    if not url.startswith('git@') and not url.startswith('https://'):
        raise argparse.ArgumentTypeError(
            '"{}" is not a cloneable git URL'.format(url)
        )
