import os

from .file import FileStorage
from .file import FileStorageWithLocalGit
from detect_secrets_server.core.usage.s3 import should_enable_s3_options


class S3Storage(FileStorage):
    """For file state management, backed to Amazon S3.

    See detect_secrets_server.storage.file.FileStorage for the expected
    file layout in the S3 bucket.
    """

    def __init__(
        self,
        base_directory,
        s3_config
    ):
        super(S3Storage, self).__init__(base_directory)

        self.access_key = s3_config['access_key']
        self.secret_access_key = s3_config['secret_access_key']
        self.bucket_name = s3_config['bucket']
        self.prefix = s3_config['prefix']

        self._initialize_client()

    def get(self, key, force_download=True):
        """Downloads file from S3 into local storage."""
        file_on_disk = self.get_tracked_file_location(key)
        if force_download or not os.path.exists(file_on_disk):
            self.client.download_file(
                Bucket=self.bucket_name,
                Key=self.get_s3_tracked_file_location(key),
                Filename=file_on_disk,
            )

        return super(S3Storage, self).get(key)

    # NOTE: There's no `put` functionality, because S3TrackedRepo handles uploads
    #       separately. That is, there are cases when you want to store a local
    #       copy, but not upload it.

    def get_tracked_repositories(self):
        # Source: https://adamj.eu/tech/2018/01/09/using-boto3-think-pagination/
        pages = self.client.get_paginator('list_objects').paginate(
            Bucket=self.bucket_name,
            Prefix=self.prefix,
        )
        for page in pages:
            for obj in page['Contents']:
                filename = os.path.splitext(obj['Key'][len(self.prefix):])[0]
                if filename.startswith('/'):
                    filename = filename[1:]

                yield (
                    self.get(filename, force_download=False),

                    # TODO: In it's current state, you can't distinguish the
                    #       difference between S3StorageWithLocalGit and S3Storage,
                    #       because there's no separate paths in S3.
                    #
                    #       Therefore, return None so that the results will be
                    #       displayed irregardless of the user's `--local` flag.
                    None,
                )

    def upload(self, key, value):
        """This is different than `put`, to support situations where you
        may want to upload locally, but not to be sync'ed with the cloud.
        """
        self.client.upload_file(
            Filename=self.get_tracked_file_location(key),
            Bucket=self.bucket_name,
            Key=self.get_s3_tracked_file_location(key),
        )

    def is_file_uploaded(self, key):
        """Note: that we are using the filename as a prefix, so we will
        never run into the 1000 object limit of `list_objects_v2`.

        :rtype: bool
        """
        filename = self.get_s3_tracked_file_location(key)
        response = self.client.list_objects_v2(
            Bucket=self.bucket_name,
            Prefix=filename,
        )

        for obj in response.get('Contents', []):
            if obj['Key'] == filename:
                return bool(obj['Size'])

        return False

    def _initialize_client(self):
        boto3 = self._get_boto3()
        if not boto3:
            return

        self.client = boto3.client(
            's3',
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_access_key,
        )

    def _get_boto3(self):
        """Used for mocking purposes."""
        if not should_enable_s3_options():
            return

        import boto3
        return boto3

    def get_s3_tracked_file_location(self, key):
        return os.path.join(
            self.prefix,
            key + '.json'
        )


class S3StorageWithLocalGit(S3Storage, FileStorageWithLocalGit):
    pass
