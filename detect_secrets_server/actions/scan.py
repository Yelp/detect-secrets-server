from __future__ import absolute_import

from detect_secrets.core.log import log

from detect_secrets_server.repos.base_tracked_repo import OverrideLevel
from detect_secrets_server.repos.factory import tracked_repo_factory

try:
    FileNotFoundError
except NameError:  # pragma: no cover
    FileNotFoundError = IOError


def scan_repo(args):
    """Returns 0 on success"""
    try:
        repo = tracked_repo_factory(
            args.local,
            bool(getattr(args, 's3_config', None)),
        ).load_from_file(
            args.repo,
            args.root_dir,
            s3_config=getattr(args, 's3_config', None),
        )
    except FileNotFoundError:
        log.error('Unable to find repo: %s', args.repo)
        return 1

    secrets = repo.scan(
        exclude_files_regex=args.exclude_files,
        exclude_lines_regex=args.exclude_lines,
    )

    if len(secrets.data) > 0:
        _alert_on_secrets_found(repo, secrets.json(), args.output_hook)

    if args.always_update_state or (
        len(secrets.data) == 0 and not args.dry_run
    ):
        _update_tracked_repo(repo)

    return 0


def _update_tracked_repo(repo):
    """Save and update records, since the latest scan indicates that the
    most recent commit is clean.
    """
    log.info('No secrets found for %s', repo.name)

    repo.update()
    repo.save(OverrideLevel.ALWAYS)


def _alert_on_secrets_found(repo, secrets, output_hook):
    """
    :type repo: detect_secrets_server.repos.base_tracked_repo.BaseTrackedRepo

    :type secrets: dict
    :param secrets: output of
        detect_secrets.core.secrets_collection.SecretsCollection.json()

    :type output_hook: detect_secrets_server.hooks.base.BaseHook
    """
    log.error('Secrets found in %s', repo.name)

    _set_authors_and_commits_for_found_secrets(repo, secrets)

    output_hook.alert(repo.name, secrets)


def _set_authors_and_commits_for_found_secrets(repo, secrets):
    """Use git blame to try and identify the user who committed the
    potential secret, and the commit. This allows us to follow up
    with a specific user if a secret is found, and reference the
    exact commit that caused the alert.

    Modifies secrets in-place.
    """
    for filename in secrets:
        for potential_secret_dict in secrets[filename]:
            blame_info = repo.storage.get_blame(
                filename,
                potential_secret_dict['line_number'],
            )
            author, commit = (
                _extract_author_and_commit_from_git_blame_info(blame_info)
            )
            potential_secret_dict['author'] = author
            potential_secret_dict['commit'] = commit


def _extract_author_and_commit_from_git_blame_info(blame_info):
    """As this tool is meant to be used in an enterprise setting, we assume
    that the email address of the committer uniquely identifies a given user.

    :type blame_info: str
    :param blame_info: output of `git blame` from git.py

    :rtype: tuple(str, str)
    :returns: author from author-mail and commit hash
    """
    blame_info = blame_info.split()

    # e.g. b5ce07a9b1a616330c1bf33799b6d06d1f9c6336 8 10 1
    commit_line = blame_info[0]
    commit_hash = commit_line.split()[0]

    index_of_mail = blame_info.index('author-mail')
    email = blame_info[index_of_mail + 1]  # e.g. `<khock@yelp.com>`
    index_of_at_symbol = email.index('@')
    # This will skip the prefix `<`, and extract the user up to the `@` sign.
    author = email[1:index_of_at_symbol]

    return author, commit_hash
