import argparse
import os

from crontab import CronSlices
from detect_secrets.core.log import log
from detect_secrets.core.usage import PluginOptions

from .common.options import CommonOptions
from .common.validators import config_file
from .common.validators import is_git_url
from .common.validators import is_valid_file


class AddOptions(CommonOptions):
    """Describes how to use this tool for initialization of tracked repos."""

    def __init__(self, subparser):
        super(AddOptions, self).__init__(subparser, 'add')

    def add_arguments(self):
        self.parser.add_argument(
            'repo',
            nargs=1,
            help=(
                'Track a repository specifying a git URL (that you would '
                '`git clone`). Newly tracked repositories will store HEAD '
                'as the last scanned commit hash.'
            ),
        )

        self.add_local_flag()\
            ._add_config_flag_argument()\
            ._add_initialize_options()\
            ._add_crontab_argument()
        PluginOptions(self.parser).add_arguments()

        return self

    def _add_config_flag_argument(self):
        """Supports the use of a config file to initialize tracked repos."""
        self.parser.add_argument(
            '--config',
            action='store_true',
            help=(
                'Indicates that the repo argument is a config file, '
                'that should be used for initializing tracked repositories.'
            ),
        )

        return self

    def _add_crontab_argument(self):
        self.parser.add_argument(
            '--crontab',
            nargs=1,
            default=['0 0 * * *'],
            type=_is_valid_crontab,
            help='Indicates the frequency which the repository should be scanned.',
        )

        return self

    def _add_initialize_options(self):
        """Users can also configure their options on the command line,
        as compared to only specifying it through a config file.
        """
        parser = self.parser.add_argument_group(
            title='settings',
        )

        parser.add_argument(
            '--baseline',
            type=str,
            nargs=1,
            help=(
                'Specify a default baseline filename to look for, within '
                'each tracked repository.'
            ),
        )

        parser.add_argument(
            '--exclude-regex',
            type=str,
            nargs=1,
            help=(
                'This regex will be added to repo metadata files when'
                'adding a repository or overriding an existing one.'
            ),
            metavar='REGEX',
        )

        return self

    @staticmethod
    def consolidate_args(args):
        """Validation and appropriate formatting of args.repo"""
        args.repo = args.repo[0]
        if args.local and args.config:
            raise argparse.ArgumentTypeError(
                'Can\'t use --config with --local.',
            )

        if args.config:
            try:
                args.repo = config_file(args.repo)['tracked']
            except KeyError:
                raise argparse.ArgumentTypeError(
                    'Invalid config file format.'
                )

            _consolidate_config_file_plugin_options(args)
        elif args.local:
            is_valid_file(args.repo)
            args.repo = os.path.abspath(args.repo)
        else:
            is_git_url(args.repo)

        _consolidate_initialize_args(args)

        # This needs to be run *after* args.repo is consolidated, so S3Options
        # can work properly.
        CommonOptions.consolidate_args(args)
        PluginOptions.consolidate_args(args)


def _consolidate_initialize_args(args):
    if args.baseline:
        args.baseline = args.baseline[0]

    if args.exclude_regex:
        args.exclude_regex = args.exclude_regex[0]

    if args.crontab:
        args.crontab = args.crontab[0]


def _consolidate_config_file_plugin_options(args):
    """
    There are three ways to configure plugin options (in order of priority):
        1. command line
        2. config file
        3. default values

    This overrides config file values with specified command line values,
    if appropriate. This is also mostly based off PluginOptions.consolidate_args
    """
    # Collect CLI specified arguments
    disabled_plugins = []
    cli_options = {}
    known_plugins = set()
    for plugin in PluginOptions.all_plugins:
        known_plugins.add(plugin.classname)

        arg_name = PluginOptions._convert_flag_text_to_argument_name(
            plugin.disable_flag_text,
        )

        is_disabled = getattr(args, arg_name)
        if is_disabled:
            disabled_plugins.append(plugin.classname)
            continue

        specified_values = {}
        for arg in plugin.related_args:
            arg_name = PluginOptions._convert_flag_text_to_argument_name(arg[0])
            specified_value = getattr(args, arg_name)
            if specified_value:
                specified_values[arg_name] = specified_value

        if specified_values:
            cli_options[plugin.classname] = specified_values

    repos = []

    # Apply it to all tracked repos
    for tracked_repo in args.repo:
        if _should_discard_tracked_repo_in_config(tracked_repo):
            continue

        if 'plugins' not in tracked_repo:
            repos.append(tracked_repo)
            continue

        # Remove unknown plugins
        unknown_plugins = filter(
            lambda name: name not in known_plugins,
            tracked_repo['plugins'].keys(),
        )
        for plugin_name in list(unknown_plugins):
            del tracked_repo['plugins'][plugin_name]

        # CLI overrides
        for plugin_classname, values in cli_options.items():
            if plugin_classname not in tracked_repo['plugins']:
                tracked_repo['plugins'][plugin_classname] = {}

            for key, value in values.items():
                tracked_repo['plugins'][plugin_classname][key] = value

        # Apply disabled plugins after setting them, to avoid strange use case
        # where user sets both the disable flag, and the custom value flag.
        # This menas that disabled plugins carry more weight than custom values.
        for disabled_plugin in disabled_plugins:
            if disabled_plugin in tracked_repo['plugins']:
                del tracked_repo['plugins'][disabled_plugin]

        repos.append(tracked_repo)

    args.repo = repos


def _should_discard_tracked_repo_in_config(tracked_repo):
    try:
        if tracked_repo.get('is_local_repo', False):
            is_valid_file(tracked_repo['repo'])
        else:
            is_git_url(tracked_repo['repo'])

        return False
    except argparse.ArgumentTypeError as e:
        # We log the error, rather than hard failing, because we don't want
        # to hard fail if one out of many repositories are bad.
        log.error(str(e))
        return True


def _is_valid_crontab(crontab):
    if CronSlices.is_valid(crontab):
        return crontab

    raise argparse.ArgumentTypeError(
        'Invalid crontab.',
    )
