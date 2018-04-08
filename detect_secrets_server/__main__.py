from __future__ import absolute_import
from __future__ import print_function

import codecs
import sys

import yaml
from detect_secrets.core.log import CustomLog

from detect_secrets_server import actions
from detect_secrets_server.repos import tracked_repo_factory
from detect_secrets_server.repos.base_tracked_repo import DEFAULT_BASE_TMP_DIR
from detect_secrets_server.repos.base_tracked_repo import OverrideLevel
from detect_secrets_server.repos.repo_config import RepoConfig
from detect_secrets_server.repos.s3_tracked_repo import S3Config
from detect_secrets_server.usage import ServerParserBuilder


CustomLogObj = CustomLog()


def open_config_file(config_file):
    try:
        with codecs.open(config_file) as f:
            data = yaml.safe_load(f)

    except IOError:
        CustomLogObj.getLogger().error(
            'Unable to open config file: %s', config_file
        )

        raise

    return data


def parse_s3_config(args):
    """
    :param args: parsed arguments from parse_args.
    :return: None if no s3_config_file specified.
    """
    if not args.s3_config_file:
        return None

    with codecs.open(args.s3_config_file[0]) as f:
        config = yaml.safe_load(f)

    try:
        return S3Config(**config)
    except TypeError:
        return None


def parse_repo_config(args):
    """
    :param args: parsed arguments from parse_args.
    :return: RepoConfig
    """
    default_repo_config = {}
    if args.config_file:
        default_repo_config = open_config_file(args.config_file[0]).get('default', {})

    return RepoConfig(
        default_repo_config.get('base_tmp_dir', DEFAULT_BASE_TMP_DIR),
        default_repo_config.get('baseline', '') or (args.baseline[0]),
        default_repo_config.get('exclude_regex', ''),
    )


def parse_args(argv):
    return ServerParserBuilder().parse_args(argv)


def main(argv=None):
    """
    Expected Usage:
      1. Initialize TrackedRepos from config.yaml, and save to crontab.
      2. Each cron command will run and scan git diff from previous commit saved, to now.
      3. If something is found, alert.

    :return: shell error code
    """
    if len(sys.argv) == 1:  # pragma: no cover
        sys.argv.append('-h')

    args = parse_args(argv)
    if args.verbose:    # pragma: no cover
        CustomLog.enableDebug(args.verbose)

    repo_config = parse_repo_config(args)
    s3_config = parse_s3_config(args)

    if args.initialize:
        output = actions.initialize.initialize(args)
        if output:
            print(output)

    elif args.add_repo:
        actions.initialize.add_repo(args)

    elif args.scan_repo:
        log = CustomLogObj.getLogger()

        repo_name = args.scan_repo[0]
        repo = tracked_repo_factory(args.local, bool(s3_config)) \
            .load_from_file(repo_name, repo_config, s3_config)
        if not repo:
            return 1

        secrets = repo.scan()

        if not secrets:
            return 1

        if len(secrets.data) > 0:
            log.error('SCAN COMPLETE - We found secrets in: %s', repo.name)

            secrets = secrets.json()
            set_authors_for_found_secrets(secrets, repo)

            alert = {
                'alert': 'Secrets found',
                'repo_name': repo.name,
                'secrets': secrets,
            }
            log.error(alert)
            args.output_hook.alert(repo.name, secrets)
        else:
            log.info('SCAN COMPLETE - STATUS: clean for %s', repo.name)

            # Save records, since the latest scan indicates that the most recent commit is clean
            repo.update()
            repo.save(OverrideLevel.ALWAYS)

    return 0


def set_authors_for_found_secrets(secrets, repo):
    """We use git blame to try and identify the user who committed the
    potential secret. This allows us to follow up with a specific user if a
    secret is found.

    :type secrets: dict
    :param secrets: output of SecretsCollection.json()

    :type repo: server.base_tracked_repo.BaseTrackedRepo
    :param repo: interface to git repository, to git blame.
    """
    for filename in secrets:
        for potential_secret_dict in secrets[filename]:
            blame_info = repo.get_blame(
                potential_secret_dict['line_number'],
                filename,
            ).split()

            potential_secret_dict['author'] = \
                _extract_user_from_git_blame_info(blame_info)


def _extract_user_from_git_blame_info(blame_info):
    """As this tool is meant to be used in an enterprise setting, we assume
    that the email address of the committer uniquely identifies a given user.

    This function extracts that information.

    :type blame_info: str
    :param blame_info: git blame info, in specific format

    :returns: unique user identifier, from email.
    """
    index_of_mail = blame_info.index('author-mail')
    email = blame_info[index_of_mail + 1]  # <khock@yelp.com>
    index_of_at = email.index('@')

    return email[1:index_of_at]  # we skip the prefix `<`, up to the `@` sign.


if __name__ == '__main__':
    sys.exit(main())
