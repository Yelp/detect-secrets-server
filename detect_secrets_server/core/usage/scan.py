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

        self.add_local_flag()
        for option in [PluginOptions, OutputOptions]:
            option(self.parser).add_arguments()

        return self

    @staticmethod
    def consolidate_args(args):
        """Validation and appropriate formatting of args.repo"""
        for option in [CommonOptions, OutputOptions]:
            option.consolidate_args(args)

        args.repo = args.repo[0]
        if args.local:
            is_valid_file(args.repo)
            args.repo = os.path.abspath(args.repo)

        PluginOptions.consolidate_args(args)
