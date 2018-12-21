from __future__ import absolute_import

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

    def get(self, key):
        """Downloads file from S3 into local storage."""
        self.client.download_file(
            self.bucket_name,
            self.get_s3_tracked_file_location(key),
            self.get_tracked_file_location(key),
        )

        return super(S3Storage, self).get(key)

    def get_tracked_repositories(self):
        # TODO
        pass

    def upload(self, key, value):
        """This is different than `put`, to support situations where you
        may want to upload locally, but not to be sync'ed with the cloud.
        """
        self.client.upload_file(
            self.get_tracked_file_location(key),
            self.bucket_name,
            self.get_s3_tracked_file_location(key),
        )

    def is_file_uploaded(self, key):
        filename = self.get_s3_tracked_file_location(key)
        response = self.client.list_objects_v2(
            Bucket=self.bucket_name,
            Prefix=filename,
        )

        for obj in response.get('Contents', []):
            if obj['Key'] == filename:
                return obj['Size']

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
        return os.path.join(self.prefix, key + '.json')


class S3StorageWithLocalGit(FileStorageWithLocalGit, S3Storage):
    pass
