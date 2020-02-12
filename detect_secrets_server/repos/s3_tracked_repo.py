from .base_tracked_repo import BaseTrackedRepo
from .base_tracked_repo import OverrideLevel
from .local_tracked_repo import LocalTrackedRepo
from detect_secrets_server.storage.s3 import S3Storage
from detect_secrets_server.storage.s3 import S3StorageWithLocalGit


class S3TrackedRepo(BaseTrackedRepo):

    STORAGE_CLASS = S3Storage

    @classmethod
    def initialize_storage(cls, base_directory):
        return cls.STORAGE_CLASS(
            base_directory,
            **cls.init_vars
        )

    def __init__(
        self,
        repo,
        sha,
        plugins,
        baseline_filename,
        exclude_regex,
        s3_config,
        crontab='',
        rootdir=None,
        *args,
        **kwargs
    ):
        """
        :type s3_config: dict
        :param s3_config: initialized in usage.S3Options. Contains the
            following keys:

            prefix: str
                an optional prefix to append to the start of the path,
                so it can be placed in the s3 bucket appropriately.

            bucket_name: str
                the bucket name to upload the meta files to

            credentials_filename: str
                filepath to s3 credentials file. This is needed for cron
                output.

            access_key: str
                s3 access key

            secret_access_key: str
                secret s3 access key
        """
        self.s3_config = s3_config

        # Store it in the class and the instance, because we need to
        # initialize_storage with the class variables.
        self._store_variables_in_class(
            s3_config=s3_config,
        )

        super(S3TrackedRepo, self).__init__(
            repo,
            sha,
            plugins,
            baseline_filename,
            exclude_regex,
            crontab,
            rootdir,
            **kwargs
        )

    @classmethod
    def load_from_file(
        cls,
        repo_name,
        base_directory,
        s3_config,
        *args,
        **kwargs
    ):
        cls._store_variables_in_class(
            s3_config=s3_config,
        )

        return super(S3TrackedRepo, cls).load_from_file(
            repo_name,
            base_directory,
        )

    @classmethod
    def get_tracked_repo_data(cls, storage, repo_name):
        output = super(S3TrackedRepo, cls).get_tracked_repo_data(storage, repo_name)
        output['s3_config'] = cls.init_vars['s3_config']

        return output

    def cron(self):     # pragma: no cover
        # TODO: deprecate this
        output = super(S3TrackedRepo, self).cron()
        return '{} --s3-credentials-file {} --s3-bucket {} --s3-prefix {}'.format(
            output,
            self.s3_config['credentials_filename'],
            self.s3_config['bucket'],
            self.s3_config['prefix'],
        )

    def save(self, override_level=OverrideLevel.ASK_USER):
        success = super(S3TrackedRepo, self).save(override_level)
        name = self.name

        is_file_uploaded = self.storage.is_file_uploaded(
            self.storage.hash_filename(name),
        )

        # Even if it does not succeed, we may still want to upload something,
        # if the file does not already exist in the s3 bucket.
        # NOTE: We leverage short-circuiting here.
        if not is_file_uploaded or (success and override_level != OverrideLevel.NEVER):
            self.storage.upload(
                self.storage.hash_filename(name),
                self.__dict__,
            )

        return success

    @classmethod
    def _store_variables_in_class(cls, **kwargs):
        """We tag these variables onto the class, so that we can take
        advantage of inheritance.
        """
        cls.init_vars = kwargs


class S3LocalTrackedRepo(S3TrackedRepo, LocalTrackedRepo):

    STORAGE_CLASS = S3StorageWithLocalGit
