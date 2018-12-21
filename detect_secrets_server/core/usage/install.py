from .common.install import get_install_options
from .common.options import CommonOptions
from .common.output import OutputOptions


class InstallOptions(CommonOptions):
    """Describes how to use this tool to install via various means."""

    def __init__(self, subparser):
        super(InstallOptions, self).__init__(subparser, 'install')

    def add_arguments(self):
        self.parser.add_argument(
            'method',
            choices=get_install_options(),
            default='cron',
            help='Method of installation.',
        )

        OutputOptions(self.parser).add_arguments()

        return self

    @staticmethod
    def consolidate_args(args):
        for option in [CommonOptions, OutputOptions]:
            option.consolidate_args(args)
