import os
from abc import ABCMeta

from .. import s3
from .storage import get_storage_options


class CommonOptions(object):
    """There are some common flags between the various different subparsers, that
    we don't want to display in the main help section.

    This contains those flags.
    """
    __metaclass__ = ABCMeta

    def __init__(self, subparser, action):
        self.parser = subparser.add_parser(action)
        self._add_common_arguments()

    def add_arguments(self):
        self.add_local_flag()

        return self

    def add_local_flag(self):
        self.parser.add_argument(
            '-L',
            '--local',
            action='store_true',
            help=(
                'Indicates that the repo argument is a locally stored '
                'repository (rather than a git URL to be cloned).'
            ),
        )

        return self

    def _add_common_arguments(self):
        self.parser.add_argument(
            '-s',
            '--storage',
            choices=get_storage_options(),
            default='file',
            help=(
                'Determines the datastore to use for storing metadata.'
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

        s3.S3Options(self.parser).add_arguments()

    @staticmethod
    def consolidate_args(args):
        args.root_dir = os.path.abspath(
            os.path.expanduser(args.root_dir[0])
        )

        s3.S3Options.consolidate_args(args)
