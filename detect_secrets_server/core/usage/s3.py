from .common.validators import config_file


def should_enable_s3_options():
    try:
        import boto3    # noqa: F401
        return True
    except ImportError:
        return False


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
            required=True,
            help='Specify keys for storing files on S3.',
            metavar='FILENAME',
        )
        self.parser.add_argument(
            '--s3-bucket',
            nargs=1,
            type=str,
            required=True,
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

        return self

    @staticmethod
    def consolidate_args(args):
        if not should_enable_s3_options():
            return

        bucket_name = args.s3_bucket[0]
        prefix = args.s3_prefix[0]
        creds_filename = args.s3_credentials_file[0]
        creds = config_file(creds_filename)

        # We don't need this anymore.
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
