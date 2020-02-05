import argparse
import os

from detect_secrets.core.usage import PluginOptions

from .common.options import CommonOptions
from .common.output import OutputOptions
from .common.validators import is_valid_file


class ScanOptions(CommonOptions):
    """Describes how to use this tool for scanning purposes."""

    def __init__(self, subparser):
        super(ScanOptions, self).__init__(subparser, 'scan')

    def add_arguments(self):
        self.parser.add_argument(
            'repo',
            nargs=1,
            help=(
                'Scans an already tracked repository by specifying a git URL '
                '(that you would `git clone`).'
            ),
        )
        self.parser.add_argument(
            '--dry-run',
            action='store_true',
            help=(
                'Scan the repository with specified plugin configuration, without '
                'saving state.'
            ),
        )
        self.parser.add_argument(
            '--scan-head',
            action='store_true',
            help=(
                'Scan the entire repo as opposed to diffs'
            ),

        )
        self.parser.add_argument(
            '--always-update-state',
            action='store_true',
            help=(
                'Always update the internal tracking state (latest commit scanned) '
                'after a successful scan, despite finding secrets.'
            ),
        )

        self.parser.add_argument(
            '--exclude-files',
            type=str,
            help=(
                'Filenames that match this regex will be ignored when '
                'scanning for secrets.'
            ),
            metavar='REGEX',
        )

        self.parser.add_argument(
            '--exclude-lines',
            type=str,
            help=(
                'Lines that match this regex will be ignored when '
                'scanning for secrets.'
            ),
            metavar='REGEX',
        )

        self.parser.add_argument(
            '--always-run-output-hook',
            action='store_true',
            help=(
                'Always run the output hook, even if no issues have been found, '
                'must be run with the --output-hook option.'
            ),
        )

        self.add_local_flag()
        for option in [PluginOptions, OutputOptions]:
            option(self.parser).add_arguments()

        return self

    @staticmethod
    def consolidate_args(args):
        """Validation and appropriate formatting of args.repo"""
        if args.dry_run and args.always_update_state:
            raise argparse.ArgumentTypeError(
                'Can\'t use --dry-run with --always-update-state.',
            )
        if (args.always_run_output_hook and (None is args.output_hook)):
            raise argparse.ArgumentTypeError(
                '--always-run-output-hook must be run with --output-hook',
            )

        for option in [CommonOptions, OutputOptions]:
            option.consolidate_args(args)

        args.repo = args.repo[0]
        if args.local:
            is_valid_file(args.repo)
            args.repo = os.path.abspath(args.repo)

        PluginOptions.consolidate_args(args)
