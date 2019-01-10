import json
import os

from .base import BaseStorage
from .base import get_filepath_safe
from .base import LocalGitRepository


class FileStorage(BaseStorage):
    """For state management without a database.

    Structure:
        root
          |- repos      # This is where git repos are cloned to
          |- tracked    # This is where meta files containing state reside
    """

    def setup(self, repo_url):
        super(FileStorage, self).setup(repo_url)

        storage_root = os.path.join(self.root, 'tracked')
        if not os.path.isdir(storage_root):
            os.makedirs(storage_root)

        return self

    def get(self, key):
        """
        :raises: FileNotFoundError
        :raises: ValueError
        """
        filename = self.get_tracked_file_location(key)
        with open(filename) as f:
            return json.load(f)

    def put(self, key, value):
        """
        :raises: ValueError
        """
        filename = self.get_tracked_file_location(key)
        with open(filename, 'w') as f:
            f.write(json.dumps(value, indent=2, sort_keys=True))

    def get_tracked_file_location(self, key):
        return get_filepath_safe(
            os.path.join(self.root, 'tracked'),
            '{}.json'.format(key),
        )

    def get_tracked_repositories(self):
        filepath = get_filepath_safe(
            self.root,
            'tracked',
        )

        for root, _, files in os.walk(filepath):
            for filename in files:
                with open(os.path.join(root, filename)) as f:
                    yield json.loads(f.read()), False

            break


class FileStorageWithLocalGit(LocalGitRepository, FileStorage):

    def setup(self, repo_url):
        super(FileStorage, self).setup(repo_url)

        storage_root = os.path.join(self.root, 'tracked')
        if not os.path.isdir(storage_root):
            os.makedirs(storage_root)

        local_storage_root = os.path.join(self.root, 'tracked', 'local')
        if not os.path.isdir(local_storage_root):
            os.makedirs(local_storage_root)

        return self

    def get_tracked_file_location(self, key):
        return get_filepath_safe(
            os.path.join(self.root, 'tracked', 'local'),
            '{}.json'.format(key),
        )

    def get_tracked_repositories(self):
        for tup in super(FileStorageWithLocalGit, self).get_tracked_repositories():
            yield tup

        filepath = get_filepath_safe(
            os.path.join(self.root, 'tracked'),
            'local',
        )

        for root, _, files in os.walk(filepath):
            for filename in files:
                with open(os.path.join(root, filename)) as f:
                    yield json.loads(f.read()), True

            break
