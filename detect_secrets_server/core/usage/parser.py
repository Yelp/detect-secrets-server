from __future__ import absolute_import

import argparse

from detect_secrets.core.usage import ParserBuilder
from detect_secrets.core.usage import PluginOptions

import detect_secrets_server
from .add import AddOptions
from .scan import ScanOptions


class ServerParserBuilder(ParserBuilder):
    """Arguments, for the server component"""

    def __init__(self):
        super(ServerParserBuilder, self).__init__()
        self._add_server_use_arguments()

    def _add_version_argument(self):
        """Overridden, because we don't want to be showing the version
        of detect-secrets plugin that we depend on.
        """
        self.parser.add_argument(
            '--version',
            action='version',
            version=detect_secrets_server.__version__,
            help='Display version information.',
        )

        return self

    def _add_server_use_arguments(self):
        subparser = self.parser.add_subparsers(
            dest='action',
        )

        for option in [AddOptions, ScanOptions]:
            option(subparser).add_arguments()

        return self

    def parse_args(self, argv):
        # NOTE: We can't just call `super`, because we need to parse the PluginOptions
        #       after we parse the config file, since we need to be able to distinguish
        #       between default values, and values that are set.
        output = self.parser.parse_args(argv)

        try:
            if output.action == 'add':
                AddOptions.consolidate_args(output)
            elif output.action == 'scan':
                ScanOptions.consolidate_args(output)
        except argparse.ArgumentTypeError as e:
            self.parser.error(e)

        PluginOptions.consolidate_args(output)
        if getattr(output, 'config', False):
            apply_default_plugin_options_to_repos(output)

        return output


def apply_default_plugin_options_to_repos(args):
    """
    There are three ways to configure options (in order of priority):
        1. command line
        2. config file
        3. default values

    This applies default values to the config file, if appropriate.
    """
    for tracked_repo in args.repo:
        if 'plugins' not in tracked_repo:
            tracked_repo['plugins'] = {}

        for key, value in args.plugins.items():
            if key not in tracked_repo['plugins']:
                tracked_repo['plugins'][key] = value

        if 'baseline' not in tracked_repo:
            tracked_repo['baseline'] = args.baseline

        if 'exclude_regex' not in tracked_repo:
            tracked_repo['exclude_regex'] = args.exclude_regex
