from .base_tracked_repo import BaseTrackedRepo
from detect_secrets_server.storage.file import FileStorageWithLocalGit


class LocalTrackedRepo(BaseTrackedRepo):

    STORAGE_CLASS = FileStorageWithLocalGit

    @property
    def name(self):
        return self.repo
