import hashlib
import os
import subprocess
from abc import ABCMeta
from abc import abstractmethod

from detect_secrets.core.log import log

from .core import git
from detect_secrets_server.util.version import is_python_2

if is_python_2():   # pragma: no cover
    FileNotFoundError = IOError
    import urlparse
else:
    import urllib.parse as urlparse


class BaseStorage(object):
    """The base class handles git interactions with the local copy
    of the git repositories.

    Structure:
        root
          |- repos      # This is where git repos are cloned to
    """
    __metaclass__ = ABCMeta

    def __init__(self, base_directory):
        self.root = base_directory

    @abstractmethod
    def get(self, key):
        """Retrieve from storage."""
        pass

    @abstractmethod
    def put(self, key, value):
        """Store in storage."""
        pass

    @abstractmethod
    def get_tracked_repositories(self):
        """Return iterator over tracked repositories.

        :rtype: (dict, bool)
            dict: metadata for tracked repo
            bool: True if local git repo
        """
        pass

    def setup(self, repo_url):
        """
        :param repo_url: this is placed in setup, rather than __init__,
            because we want to use this class without pinning it down
            to a repository.

            e.g. We should be able to retrieve information about the
            repo_url from a file, with delayed setup.

        :returns: self, for better chaining
        """
        self.repo_url = repo_url

        if not os.path.isdir(self.root):
            os.makedirs(self.root)

        self._initialize_git_repos_directory()

        return self

    @property
    def repository_name(self):
        """Human friendly name of git repository tracked."""
        return self.get_repo_name(self.repo_url)

    def clone(self):
        git.clone_repo_to_location(
            self.repo_url,
            self._repo_location,
        )

    def fetch_new_changes(self):
        git.fetch_new_changes(self._repo_location)

    def get_diff(self, from_sha, filename=None):
        try:
            return git.get_diff(self._repo_location, from_sha, files=[filename])
        except subprocess.CalledProcessError:
            # This sometimes complains, if the hash does not exist.
            # There could be a variety of reasons for this, including:
            #    - some sort of rewrite of git history
            #    - this scanner being run on an out-of-date repo
            #
            # To prevent from any further alerting on this, we are going to
            # update the last_commit_hash, to prevent re-alerting on old
            # secrets.
            #
            # TODO: Fix this to be more robust.
            log.error(
                self._construct_debugging_output(from_sha),
            )

            raise

    def get_diff_name_only(self, from_sha):
        return git.get_diff_name_only(self._repo_location, from_sha)

    def _construct_debugging_output(self, sha):  # pragma: no cover
        alert = {
            'alert': 'Hash not found during git diff',
            'hash': sha,
            'repo_location': self._repo_location,
            'repo_name': self.repository_name,
        }

        if not os.path.exists(self._repo_location):
            alert['info'] = 'repo_location does not exist'
            return alert

        path_to_HEAD = os.path.join(self._repo_location, '/logs/HEAD')
        if not os.path.exists(path_to_HEAD):
            alert['info'] = 'logs/HEAD does not exist'
            return alert

        try:
            with open(path_to_HEAD) as f:
                first_line = f.readline().strip()
        except FileNotFoundError:
            first_line = ''

        alert['info'] = 'first_line of logs/HEAD is {}'.format(
            str(first_line),
        )
        return alert

    def get_last_commit_hash(self):
        return git.get_last_commit_hash(self._repo_location)

    def get_baseline_file(self, baseline_filename):
        return git.get_baseline_file(
            self._repo_location,
            baseline_filename,
        )

    def get_blame(self, filename, line_number):
        return git.get_blame(
            self._repo_location,
            filename,
            line_number,
        )

    @staticmethod
    def hash_filename(name):
        """Function broken out, so it can be referenced in test cases"""
        return hashlib.sha512(name.encode('utf-8')).hexdigest()

    def get_repo_name(self, url):
        """Function broken out, so can be extended in subclass.

        Example: 'git@github.com:yelp/detect-secrets' => yelp/detect-secrets
        """
        if url.startswith('git@'):
            name = url.split(':')[1]
        else:
            components = urlparse.urlparse(url)
            name = components.path.lstrip('/')

        if name.endswith('.git'):
            return name[:-4]

        return name

    def _initialize_git_repos_directory(self):
        git_repos_root = os.path.join(self.root, 'repos')
        if not os.path.isdir(git_repos_root):
            os.makedirs(git_repos_root)

    @property
    def _repo_location(self):
        return get_filepath_safe(
            os.path.join(self.root, 'repos'),
            self.hash_filename(self.repository_name),
        )


class LocalGitRepository(BaseStorage):
    """This mixin surpresses some automated management for git repositories,
    for cases when you already have the git repository on your system, and
    want to scan that (instead of having this system track it for you).

    Since this surpresses parent functionality, the declaration order for
    the mixin is important.

    Example:
        >>> class Example(LocalGitRepository, FileStorage):
        ...     pass

    Structure:
        root
          |- tracked
                |- local   # meta files for local tracked repositories
    """

    @property
    def repository_name(self):
        """Human friendly name of git repository tracked.

        Example: 'git@github.com:yelp/detect-secrets' => yelp/detect-secrets
        """
        path = self.repo_url
        if not path.endswith('/.git'):
            path = os.path.join(path, '.git')

        return super(LocalGitRepository, self).get_repo_name(
            git.get_remote_url(path),
        )

    def clone(self):
        """If it is locally on disk, no need to clone it."""
        return

    def fetch_new_changes(self):
        """The assumption is, if you are scanning a local git repository,
        then you are "actively" working on it. Therefore, this module will
        not bear the responsibility of auto-updating the repo with `git fetch`.
        """
        return

    def _initialize_git_repos_directory(self):
        """Don't need to create a place for tracking git repos"""
        return

    @property
    def _repo_location(self):
        """When we're performing git commands on a local repository, we need
        to reference the `/.git` folder within the cloned git repo.

        Unless it is a local bare repo.
        """
        inner_git_dir = os.path.join(self.repo_url, '.git')
        if os.path.exists(inner_git_dir):
            return inner_git_dir
        # Bare repo
        return self.repo_url


def get_filepath_safe(prefix, file):
    """Attempts to prevent file traversal when trying to get `prefix/file`"""
    prefix_realpath = os.path.realpath(prefix)
    filepath = os.path.realpath(
        '%(prefix_realpath)s/%(file)s' % {
            'prefix_realpath': prefix_realpath,
            'file': file,
        }
    )
    if not filepath.startswith(prefix_realpath):
        raise ValueError

    return filepath
