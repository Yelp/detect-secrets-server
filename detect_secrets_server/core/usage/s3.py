import argparse

from .common.storage import should_enable_s3_options
from .common.validators import config_file
from .common.validators import json_file


class S3Options(object):

    def __init__(self, parser):
        self.parser = None
        if not should_enable_s3_options():
            return

        self.parser = parser.add_argument_group(
            title='s3 storage settings',
            description=(
                'Configure options for using Amazon S3 as a storage option.'
            ),
        )

    def add_arguments(self):
        if not self.parser:
            return self

        self.parser.add_argument(
            '--s3-credentials-file',
            nargs=1,
            type=str,
            help='Specify keys for storing files on S3.',
            metavar='FILENAME',
        )
        self.parser.add_argument(
            '--s3-bucket',
            nargs=1,
            type=str,
            help='Specify which bucket to perform S3 operations on.',
            metavar='BUCKET_NAME',
        )
        self.parser.add_argument(
            '--s3-prefix',
            nargs=1,
            type=str,
            default=[''],
            help='Specify the path prefix within the S3 bucket.',
            metavar='PREFIX',
        )
        self.parser.add_argument(
            '--s3-config',
            nargs=1,
            type=config_file,
            default=None,
            help='Specify config file for all S3 config options.',
            metavar='CONFIG_FILE',
        )

        return self

    @staticmethod
    def consolidate_args(args):
        if not _needs_s3_config(args):
            return

        try:
            args.s3_config = args.s3_config[0]
        except AttributeError:
            raise argparse.ArgumentTypeError(
                'Please pip install the `boto3` library.'
            )
        except TypeError:
            # If nothing is specified, then args.s3_config == None.
            # This is sufficient for conditional logic to determine whether
            # user supplied a config file.
            pass

        if args.s3_config and any([
            args.s3_bucket,
            args.s3_credentials_file,
            args.s3_prefix[0],
        ]):
            raise argparse.ArgumentTypeError(
                'Can\'t specify --s3-config with other s3 command line arguments.',
            )
        elif not args.s3_config and not all([
            args.s3_credentials_file,
            args.s3_bucket,
        ]):
            raise argparse.ArgumentTypeError(
                'the following arguments are required: --s3-credentials-file, --s3-bucket',
            )

        if args.s3_config:
            bucket_name = args.s3_config['bucket_name']
            prefix = args.s3_config['prefix']
            creds_filename = args.s3_config['credentials_filename']
        else:
            bucket_name = args.s3_bucket[0]
            prefix = args.s3_prefix[0]
            creds_filename = args.s3_credentials_file[0]

        creds = json_file(creds_filename)

        # We do not need these anymore.
        del args.s3_bucket
        del args.s3_prefix
        del args.s3_credentials_file

        args.s3_config = {
            'prefix': prefix,
            'bucket': bucket_name,
            'creds_filename': creds_filename,
            'access_key': creds['accessKeyId'],
            'secret_access_key': creds['secretAccessKey'],
        }


def _needs_s3_config(args):
    if args.storage == 's3':
        return True

    if args.action == 'add' and args.config:
        for repo in args.repo:
            if repo.get('storage') == 's3':
                return True

    return False
