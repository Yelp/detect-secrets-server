"""Collection of all git command interactions"""
import os
import re
import subprocess
import sys

from detect_secrets.core.log import log

from detect_secrets_server.constants import IGNORED_FILE_EXTENSIONS

GIT_EMPTY_TREE_HASH = '4b825dc642cb6eb9a060e54bf8d69288fbee4904'


def get_last_commit_hash(directory):
    return _git(
        directory,
        'rev-parse',
        'HEAD',
    )


def get_empty_tree_commit_hash():
    return GIT_EMPTY_TREE_HASH


def clone_repo_to_location(repo, directory):
    """
    :type repo: str
    :param repo: git url to clone

    :type directory: str
    :param directory: local directory path
    """
    try:
        # We need to run it through check_output, because we want to trigger
        # a subprocess.CalledProcessError upon failure.
        subprocess.check_output([
            'git', 'clone',
            repo,
            directory,

            # We clone a bare repo, because we're not interested in the
            # files themselves. This will be more space efficient.
            '--bare',
        ], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        error_message = e.output.decode('utf-8')

        # Ignore this message, because it's expected if the repo
        # has already been tracked.
        if not re.match(
            r"fatal: destination path '[^']+' already exists",
            error_message
        ):
            raise


def fetch_new_changes(directory):
    main_branch = _get_main_branch(directory)
    _git(
        directory,
        'fetch',
        '--quiet',
        'origin',
        '{}:{}'.format(
            main_branch,
            main_branch,
        ),
        '--force',
    )


def get_baseline_file(directory, filename):
    """Take the most updated baseline, because want to get the most updated
    baseline. Note that this means it's still "user-dependent", but at the
    same time, we want to ignore new explicit whitelists.
    Also, this would mean that we **always** get a whitelist, if exists
    (rather than worrying about fixing on a commit that has a whitelist)

    :returns: file contents of baseline_file
    """
    try:
        return _git(
            directory,
            'show', 'HEAD:{}'.format(filename),
        )

    except subprocess.CalledProcessError as e:
        error_message = e.output.decode('utf-8')

        # Some repositories may not have baselines.
        # If so, this is a non-breaking error.
        if not (
            re.match(
                r"fatal: Path '[^']+' does not exist",
                error_message,
            )
            or
            # It is possible for the directory you are running detect-secret-server from
            # to also contain a file with the name <secrets baseline filename>, but
            # is not part of the repo being scanned.
            # This will create a different error message, which we also want to catch.
            re.match(
                r"fatal: Path '[^']+' exists on disk, but not in 'HEAD'",
                error_message,
            )
        ):
            raise


def get_diff(directory, last_commit_hash, files=None):
    """Returns the git diff between last commit hash, and HEAD."""
    kwargs = {'should_strip_output': False}
    git_args = [
        directory,
        'diff',
        last_commit_hash,
        'HEAD',
    ]

    if not files:
        filenames_to_include_in_diff = _filter_filenames_from_diff(directory, last_commit_hash)
    else:
        filenames_to_include_in_diff = files

    if (
        filenames_to_include_in_diff
        and
        # This happens when there are too many files in the diff
        # e.g. 'warning: inexact rename detection was skipped due to too many files.'
        # We choose to not include specific files out in this case
        # Because if we did, we would later get a
        # `OSError: [Errno 7] Argument list too long`
        # when including the list of files.
        not filenames_to_include_in_diff[-1].startswith('warning:')
    ):
        git_args.extend(
            ['--'] + filenames_to_include_in_diff,
        )

    return _git(
        *git_args,
        # Python 2 made me do this
        **kwargs
    )


def get_diff_name_only(directory, last_commit_hash):
    return _filter_filenames_from_diff(directory, last_commit_hash)


def get_remote_url(directory):
    return _git(
        directory,
        'remote',
        'get-url',
        'origin',
    )


def get_blame(directory, filename, line_number):
    """Returns the author who last made the change, to a given file,
    on a given line.
    """
    return _git(
        directory,
        'blame',
        _get_main_branch(directory),
        '-L', '{},{}'.format(line_number, line_number),
        '--show-email',
        '--line-porcelain',
        '--',
        filename,
    )


def _get_main_branch(directory):
    """While this is `master` most of the time, there are some exceptions"""
    return _git(
        directory,
        'rev-parse',
        '--abbrev-ref',
        'HEAD',
    )


def _filter_filenames_from_diff(directory, last_commit_hash):
    filenames = _git(
        directory,
        'diff',
        last_commit_hash,
        'HEAD',
        '--name-only',
        '--diff-filter', 'ACM',
    ).splitlines()

    return [
        filename
        for filename in filenames
        if os.path.splitext(filename)[1] not in IGNORED_FILE_EXTENSIONS
    ]


def _git(directory, *args, **kwargs):
    try:
        output = subprocess.check_output(
            [
                'git',
                '--git-dir', directory,
            ] + list(args),
            stderr=subprocess.STDOUT
        ).decode('utf-8', errors='ignore')

        # This is to fix https://github.com/matiasb/python-unidiff/issues/54
        if not kwargs.get('should_strip_output', True):
            return output
        return output.strip()
    except subprocess.CalledProcessError as e:
        error_message = e.output.decode('utf-8')

        # Catch this error, this happens during scanning and means it's an empty repo. This bails out
        # of the scan process and logs error.
        if re.match(
            r"fatal: couldn't find remote ref (None|HEAD)",
            error_message
        ):
            # directory is the best/only output without drastic rewrites, hashed path correlates to repo
            log.error("Empty repository cannot be scanned: %s", directory)
            sys.exit(1)
            # TODO: This won't work if scan loops through repos, but works since it's a single scan currently

        # Catch this error, this happens during initialization and means it's an empty repo. This allows
        # the repo metadata to be written to /tracked
        elif re.match(
                r"fatal: ambiguous argument 'HEAD': unknown revision or path not in the working tree.",
                error_message
        ):
            return None
        else:
            raise
