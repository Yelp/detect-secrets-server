import os
import subprocess
import sys
from enum import Enum

from detect_secrets.core.baseline import get_secrets_not_in_baseline
from detect_secrets.core.secrets_collection import SecretsCollection
from detect_secrets.plugins.common import initialize as initialize_plugins

from detect_secrets_server.storage.core import git
from detect_secrets_server.storage.file import FileStorage


class OverrideLevel(Enum):
    NEVER = 0
    ASK_USER = 1
    ALWAYS = 2


class BaseTrackedRepo(object):

    # This should be overriden in subclasses.
    STORAGE_CLASS = FileStorage

    @classmethod
    def initialize_storage(cls, base_directory):
        return cls.STORAGE_CLASS(base_directory)

    def __init__(
        self,
        repo,
        sha,
        plugins,
        baseline_filename,
        exclude_regex,
        crontab='',
        rootdir=None,
        **kwargs
    ):
        """
        :type repo: str
        :param repo: git URL or local path of repo

        :type sha: str
        :param sha: last commit hash scanned

        :type plugins: dict
        :param plugins: values to configure various plugins, formatted as
            described in detect_secrets.core.usage

        :type rootdir: str
        :param rootdir: the directory to clone git repositories to.

        :type exclude_regex: str
        :param exclude_regex: used for repository scanning; if a filename
            matches this exclude_regex, it is not scanned.

        :type crontab: str
        :param crontab: crontab syntax, for periodic scanning.

        :type baseline_filename: str
        :param baseline_filename: each repository may have a different
            baseline filename. This allows us to customize these filenames
            per repository.
        """
        self.last_commit_hash = sha
        self.repo = repo
        self.crontab = crontab
        self.plugin_config = plugins
        self.baseline_filename = baseline_filename
        self.exclude_regex = exclude_regex

        if rootdir:
            self.storage = self.initialize_storage(rootdir).setup(repo)

    @classmethod
    def load_from_file(
        cls,
        repo_name,
        base_directory,
        *args,
        **kwargs
    ):
        """This will load a TrackedRepo to memory, from a given meta tracked
        file. For automated management without a database.

        The meta tracked file is in the format of self.__dict__

        :type repo_name: str
        :param repo_name: If the git URL is `git@github.com:yelp/detect-secrets`
            this value will be `yelp/detect-secrets`

        :rtype: TrackedRepo
        :raises: FileNotFoundError
        """
        storage = cls.initialize_storage(base_directory)

        data = cls.get_tracked_repo_data(storage, repo_name)

        output = cls(**data)
        output.storage = storage.setup(output.repo)

        return output

    @classmethod
    def get_tracked_repo_data(cls, storage, repo_name):
        if repo_name.startswith('git@') or repo_name.startswith('http'):
            repo_name = storage.get_repo_name(repo_name)

        return storage.get(storage.hash_filename(repo_name))

    @property
    def name(self):
        return self.storage.repository_name

    def scan(self, exclude_files_regex=None, exclude_lines_regex=None, scan_head=False):
        """Fetches latest changes, and scans the git diff between last_commit_hash
        and HEAD.

        :raises: subprocess.CalledProcessError

        :type exclude_files_regex: str|None
        :param exclude_files_regex: A regex matching filenames to skip over.

        :type exclude_lines: str|None
        :param exclude_lines: A regex matching lines to skip over.

        :rtype: SecretsCollection
        :returns: secrets found.
        """
        self.storage.fetch_new_changes()

        default_plugins = initialize_plugins.from_parser_builder(
            self.plugin_config,
            exclude_lines_regex=exclude_lines_regex,
        )
        # TODO Issue 17: Ignoring self.exclude_regex, using the server scan CLI arg
        secrets = SecretsCollection(
            plugins=default_plugins,
            exclude_files=exclude_files_regex,
            exclude_lines=exclude_lines_regex,
        )

        scan_from_this_commit = git.get_empty_tree_commit_hash() if scan_head else self.last_commit_hash
        try:
            diff_name_only = self.storage.get_diff_name_only(scan_from_this_commit)

            # do a per-file diff + scan so we don't get a OOM if the the commit-diff is too large
            for filename in diff_name_only:
                file_diff = self.storage.get_diff(scan_from_this_commit, filename)

                secrets.scan_diff(
                    file_diff,
                    baseline_filename=self.baseline_filename,
                    last_commit_hash=scan_from_this_commit,
                    repo_name=self.name,
                )
        except subprocess.CalledProcessError:
            self.update()
            return secrets

        if self.baseline_filename:
            baseline = self.storage.get_baseline_file(self.baseline_filename)
            if baseline:
                baseline_collection = SecretsCollection.load_baseline_from_string(baseline)
                secrets = get_secrets_not_in_baseline(secrets, baseline_collection)

        return secrets

    def update(self):
        self.last_commit_hash = self.storage.get_last_commit_hash()

    def save(self, override_level=OverrideLevel.ASK_USER):
        """Saves tracked repo config to file. Returns True if successful.

        :type override_level: OverrideLevel
        :param override_level: determines if we overwrite the JSON file, if exists.

        :rtype: bool
        :returns: True if repository is saved.
        """
        name = self.name
        if os.path.isfile(
            self.storage.get_tracked_file_location(
                self.storage.hash_filename(name),
            )
        ):
            if override_level == OverrideLevel.NEVER:
                return False

            elif override_level == OverrideLevel.ASK_USER:
                if not self._prompt_user_override():
                    return False

        self.storage.put(
            self.storage.hash_filename(name),
            self.__dict__,
        )

        return True

    @property
    def __dict__(self):
        """This is written to the filesystem, and used in load_from_file.
        Should contain all variables needed to initialize TrackedRepo."""
        output = {
            'repo': self.repo,
            'sha': self.last_commit_hash,
            'crontab': self.crontab,

            'baseline_filename': self.baseline_filename,
            'exclude_regex': self.exclude_regex,

            'plugins': self.plugin_config,
        }

        return output

    def _prompt_user_override(self):  # pragma: no cover
        """Prompts for user input to check if should override file.

        :rtype: bool
        """
        # Make sure to write to stderr, because crontab output is going to be to stdout
        sys.stdout = sys.stderr

        override = None
        while override not in ['y', 'n']:
            override = str(
                input(
                    '"{}" repo already tracked! Do you want to override this (y|n)? '.format(
                        self.name,
                    )
                )
            ).lower()

        sys.stdout = sys.__stdout__

        if override == 'n':
            return False

        return True
