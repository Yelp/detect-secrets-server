import json
import os

import boto3

from .file import FileStorage
from .file import FileStorageWithLocalGit


class S3Storage(FileStorage):
    """For file state management, backed to Amazon S3.

    See detect_secrets_server.storage.file.FileStorage for the expected
    file layout in the S3 bucket.
    """

    def __init__(
        self,
        base_directory,
        credentials_filename,
        bucket_name,
        prefix='',
    ):
        super(S3Storage, self).__init__(base_directory)

        self.credentials_filename = credentials_filename
        self.bucket_name = bucket_name
        self.prefix = prefix

        self._initialize_client()

    def get(self, key):
        """Downloads file from S3 into local storage."""
        self.client.download_file(
            self.bucket_name,
            self.get_s3_tracked_file_location(key),
            self.get_tracked_file_location(key),
        )

        return super(S3Storage, self).get(key)

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
        with open(self.credentials_filename) as f:
            credentials = json.load(f)

        self.client = boto3.client(
            's3',
            aws_access_key_id=credentials['accessKeyId'],
            aws_secret_access_key=credentials['secretAccessKey'],
        )

    def get_s3_tracked_file_location(self, key):
        return os.path.join(self.prefix, key + '.json')


class S3StorageWithLocalGit(FileStorageWithLocalGit, S3Storage):
    pass
