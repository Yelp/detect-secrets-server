from __future__ import absolute_import

import codecs
import hashlib
import json
import os
import subprocess
import sys
from enum import Enum

from detect_secrets.core.baseline import get_secrets_not_in_baseline
from detect_secrets.core.log import CustomLog
from detect_secrets.core.secrets_collection import SecretsCollection
from detect_secrets.plugins import initialize_plugins

from . import git
from detect_secrets_server.plugins import PluginsConfigParser


DEFAULT_BASE_TMP_DIR = os.path.expanduser('~/.detect-secrets-server')

CustomLogObj = CustomLog()


class OverrideLevel(Enum):
    NEVER = 0
    ASK_USER = 1
    ALWAYS = 2


def get_filepath_safe(prefix, file):
    """Attempts to prevent file traversal when trying to get `prefix/file`"""
    prefix_realpath = os.path.realpath(prefix)
    filepath = os.path.realpath('%(prefix_realpath)s/%(file)s' % {'prefix_realpath': prefix_realpath, 'file': file})
    if not filepath.startswith(prefix_realpath):
        return None

    return filepath


class BaseTrackedRepo(object):

    def __init__(
            self,
            sha,
            repo,
            plugins,
            base_temp_dir,
            baseline_filename,
            exclude_regex,
            cron='',
            **kwargs
    ):
        """
        :type sha: string
        :param sha: last commit hash scanned

        :type repo: string
        :param repo: git URL or local path of repo

        :type plugins: dict
        :param plugins: values to configure various plugins

        :type cron: string
        :param cron: crontab syntax
        """
        self.last_commit_hash = sha
        self.repo = repo
        self.crontab = cron
        self.plugin_config = plugins
        self.base_tmp_dir = base_temp_dir
        self.baseline_file = baseline_filename
        self.exclude_regex = exclude_regex

        self.name = self._get_repo_name(repo)

        self._initialize_tmp_dir(base_temp_dir)

    @classmethod
    def load_from_file(
            cls,
            repo_name,
            base_temp_dir,
            baseline_filename,
            exclude_regex,
            *args,
            **kwargs
    ):
        """This will load a TrackedRepo to memory, from a given tracked file.
        For automated management without a database.

        :type repo_name: string
        :param repo_name: git URL or local path of repo

        :return: TrackedRepo
        """
        repo_name = cls._get_repo_name(repo_name)

        data = cls._read_tracked_file(repo_name, base_temp_dir)
        if data is None:
            return None

        data = cls._modify_tracked_file_contents(data)

        # Add server-side configuration to repo
        data['base_temp_dir'] = base_temp_dir
        data['baseline_filename'] = baseline_filename
        data['exclude_regex'] = exclude_regex

        return cls(**data)

    def cron(self):
        """Returns the cron command to be appended to crontab"""
        return '%(crontab)s    detect-secrets-server --scan-repo %(name)s' % {
            'crontab': self.crontab,
            'name': self.name,
        }

    def scan(self):
        """Clones the repo, and scans the git diff between last_commit_hash and HEAD.

        :raises: subprocess.CalledProcessError
        """
        self.clone_and_pull_repo()
        diff = self._get_latest_changes()
        baseline = git.get_baseline_file(
            self.repo_location,
            self.baseline_file,
        )

        default_plugins = initialize_plugins(self.plugin_config)

        secrets = SecretsCollection(default_plugins, self.exclude_regex)

        secrets.scan_diff(
            diff,
            baseline_filename=baseline,
            last_commit_hash=self.last_commit_hash,
            repo_name=self.name
        )

        if baseline:
            baseline_collection = SecretsCollection.load_baseline_from_string(baseline)
            secrets = get_secrets_not_in_baseline(secrets, baseline_collection)

        return secrets

    def update(self):
        """Updates TrackedRepo to latest commit.

        :raises: subprocess.CalledProcessError
        """
        self.last_commit_hash = git.get_last_commit_hash(self.repo_location)

    def save(self, override_level=OverrideLevel.ASK_USER):
        """Saves tracked repo config to file. Returns True if successful.

        :type override_level: OverrideLevel
        :param override_level: determines if we overwrite the JSON file, if exists.
        """
        if self.tracked_file_location is None:
            return False

        # If file exists, check OverrideLevel
        if os.path.isfile(self.tracked_file_location):
            if override_level == OverrideLevel.NEVER:
                return False

            elif override_level == OverrideLevel.ASK_USER:
                if not self._prompt_user_override():
                    return False

        with codecs.open(self.tracked_file_location, 'w') as f:
            f.write(json.dumps(self.__dict__, indent=2))

        return True

    @property
    def repo_location(self):
        return get_filepath_safe(
            '%s/repos' % self.base_tmp_dir,
            self.internal_filename
        )

    @property
    def internal_filename(self):
        return self.hash_filename(self.name)

    @staticmethod
    def hash_filename(name):
        """Used, so that it can be referenced in test cases"""
        return hashlib.sha512(name.encode('utf-8')).hexdigest()

    @property
    def tracked_file_location(self):
        return self._get_tracked_file_location(
            self.base_tmp_dir,
            self.internal_filename
        )

    @classmethod
    def _initialize_tmp_dir(self, base_tmp_dir):  # pragma: no cover
        """Make base tmp folder, if non-existent."""
        if not os.path.isdir(base_tmp_dir):
            os.makedirs(base_tmp_dir)
            os.makedirs(base_tmp_dir + '/repos')
            os.makedirs(base_tmp_dir + '/tracked')

    @classmethod
    def _get_repo_name(cls, url):
        """Obtains the repo name repo URL.
        This allows for local file saving, as compared to the URL, which indicates WHERE to clone from.

        :type url: string
        """
        # e.g. 'git@github.com:pre-commit/pre-commit-hooks' -> pre-commit/pre-commit-hooks
        name = url.split(':')[-1]

        # The url_or_path will still work without the `.git` suffix.
        if name.endswith('.git'):
            return name[:-4]

        return name

    def clone_and_pull_repo(self):
        """We want to update the repository that we're tracking, to get the latest changes.
        Then, we can subsequently scan these new changes.

        :raises: subprocess.CalledProcessError
        """
        git.clone_repo_to_location(self.repo, self.repo_location)
        git.pull_master(self.repo_location)

    def get_blame(self, filename, line_number):
        """
        :return: string

        :raises: subprocess.CalledProcessError
        """
        return git.get_blame(self.repo_location, filename, line_number)

    def _get_latest_changes(self):  # pragma: no cover
        """
        :return: string
                 This will be the patch file format of difference between last saved "clean"
                 commit hash, and HEAD.

        :raises: subprocess.CalledProcessError
        """
        try:
            return git.get_diff(self.repo_location, self.last_commit_hash)
        except subprocess.CalledProcessError:
            # Some debugging output for this strange case
            repo_location_exists = os.path.exists(self.repo_location)
            head_exists = os.path.exists(self.repo_location + '/logs/HEAD')
            first_line = ''
            if head_exists:
                with open(self.repo_location + '/logs/HEAD', 'r') as f:
                    first_line = f.readline().strip()
            alert = {
                'alert': 'Hash not found when diffing',
                'hash': self.last_commit_hash,
                'repo_location': self.repo_location,
                'repo_name': self.name,
            }
            if not repo_location_exists:
                alert['info'] = 'self.repo_location does not exist'
            elif not head_exists:
                alert['info'] = 'logs/HEAD does not exist'
            else:
                alert['info'] = 'first_line of logs/HEAD is ' + str(first_line)
            CustomLogObj.getLogger().error(alert)

            # The last_commit_hash may have been removed from the git logs,
            # or detect-secrets is being run on an out-of-date repo, in which
            # case it may re-alert on old secrets now.
            self.update()
            return ''

    @classmethod
    def get_tracked_filepath_prefix(cls, base_tmp_dir):
        """Returns the directory where the tracked file lives on disk."""
        return '%s/tracked' % base_tmp_dir

    @classmethod
    def _get_tracked_file_location(cls, base_tmp_dir, internal_filename):
        """We use the file system (instead of a DB) to track and monitor changes to
        all TrackedRepos. This function returns where this file lives.

        :return: string
        """
        return get_filepath_safe(
            cls.get_tracked_filepath_prefix(base_tmp_dir),
            internal_filename + '.json'
        )

    @classmethod
    def _read_tracked_file(cls, repo_name, base_tmp_dir):
        """
        :type repo_name: string
        :param repo_name: name of repo to scan
        :return: TrackedRepo __dict__ representation
        """
        # We need to manually get the `internal_name` of the repo, to know which file to read from.
        filename = cls._get_tracked_file_location(
            base_tmp_dir,
            hashlib.sha512(repo_name.encode('utf-8')).hexdigest()
        )
        if not filename:
            return None

        try:
            with codecs.open(filename) as f:
                return json.loads(f.read())
        except (IOError, ValueError, TypeError):
            CustomLogObj.getLogger().error(
                'Unable to open repo data file: %s. Aborting.', filename,
            )
            return None

    def _prompt_user_override(self):  # pragma: no cover
        """Prompts for user input to check if should override file.
        :return: bool
        """
        # Make sure to write to stderr, because crontab output is going to be to stdout
        sys.stdout = sys.stderr

        override = None
        while override not in ['y', 'n']:
            override = str(input(
                '"%s" repo already tracked! Do you want to override this (y|n)? ' % self.name
            )).lower()

        sys.stdout = sys.__stdout__

        if override == 'n':
            return False
        return True

    @classmethod
    def _modify_tracked_file_contents(cls, data):
        """For better representation, we use namedtuples. However, these do not directly
        correlate to file dumps (which `save` does, using `__dict__`. Therefore, we may
        need to modify these values, before loading them into the class constructor.

        :type data: dict
        :param data: pretty much the layout of __dict__
        :return: dict
        """
        data['plugins'] = PluginsConfigParser.from_config(data['plugins']).to_args()

        return data

    @property
    def __dict__(self):
        """This is written to the filesystem, and used in load_from_file.
        Should contain all variables needed to initialize TrackedRepo."""
        output = {
            'sha': self.last_commit_hash,
            'repo': self.repo,
            'plugins': PluginsConfigParser.from_args(self.plugin_config).to_config(),
            'cron': self.crontab,
            'baseline_file': self.baseline_file,
        }

        return output
