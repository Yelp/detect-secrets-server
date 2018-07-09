from __future__ import absolute_import

from detect_secrets_server.plugins import PluginsConfigParser
from detect_secrets_server.repos.base_tracked_repo import OverrideLevel
from detect_secrets_server.repos.factory import tracked_repo_factory


def add_repo(args):
    """Sets up an individual repository for tracking."""
    repo_class = tracked_repo_factory(
        args.local,
        bool(getattr(args, 's3_config', None)),
    )

    repo = repo_class(
        repo=args.repo,

        # Will be updated to HEAD upon first update
        sha='',

        # TODO: Comment
        cron='',

        plugins=args.plugins,
        base_temp_dir=args.root_dir,
        baseline_filename=args.baseline,
        exclude_regex=args.exclude_regex,

        s3_config=getattr(args, 's3_config', None),
    )

    _clone_and_save_repo(repo)


def initialize(args):
    """Initializes a list of repositories from a specified repos.yaml,
    and returns the commands to add to your crontab.

    Sets up local file storage for tracking repositories.
    """
    tracked_repos = _load_from_config(
        args.repo,
        args.plugins,
        args.root_dir,
        args.baseline,
        args.exclude_regex,
    )

    cron_repos = [repo for repo in tracked_repos if _clone_and_save_repo(repo)]
    if not cron_repos:
        return

    output = '# detect-secrets scanner'
    for repo in cron_repos:
        output += '\n{} {}'.format(
            repo.cron(),
            args.output_hook_command,
        )

    return output


def _clone_and_save_repo(repo):
    """
    :type repo: BaseTrackedRepo
    :param repo: repo to clone (if appropriate) and save
    """
    # Clone repo, if needed.
    repo.storage.clone_and_pull_master()

    # Make the last_commit_hash of repo point to HEAD
    if not repo.last_commit_hash:
        repo.update()

    # Save the last_commit_hash, if we have nothing on file already
    return repo.save(OverrideLevel.NEVER)


def _load_from_config(
    repos,
    default_plugins,
    base_temp_dir,
    baseline_filename,
    exclude_regex
):
    """For expected config format, see `examples/repos.yaml`.

    :type repos: dict
    :param repos: content of repos.yaml

    :type default_plugins: dict
    :param default_plugins: output of
        detect_secrets.core.usage.PluginOptions.consolidate_args

    :type base_temp_dir: str
    :type baseline_filename: str
    :type exclude_regex: str

    :returns: list of TrackedRepos
    :raises: IOError
    """
    output = []
    if not repos.get('tracked'):
        return output

    for entry in repos['tracked']:
        output.append(
            _initialize_repo_from_config_entry(
                entry,
                default_plugins,
                base_temp_dir,
                baseline_filename,
                exclude_regex,
            )
        )

    return output


def _initialize_repo_from_config_entry(
    entry,
    default_plugins,
    base_temp_dir,
    baseline_filename,
    exclude_regex
):
    """
    :type entry: dict
    :param entry: supports the following options
        Required arguments:
            repo: str
                The url to clone, in `git clone <url>`.
            sha: str
                Last commit hash scanned.
            cron: str
                crontab syntax, denoting frequency of repo scan.

        Arguments that can have global defaults:
            plugins: dict
                mapping of plugin classnames to initialization values.
            baseline_file: str
                repo-specific filename of baseline file.
            exclude_regex: str
                filenames that match this regex will be excluded from scanning.

        Optional arguments include:
            is_local_repo: bool
                indicates that repository is locally stored (no need to git clone)
            s3_backend: bool
                files generated to save state will be synced with Amazon S3.

        These entries take precedence over default options.

    :type default_plugins: dict
    :type base_temp_dir: str
    :type baseline_filename: str
    :type exclude_regex: str
    """
    if entry.get('plugins'):
        default_plugins = PluginsConfigParser.from_args(default_plugins)
        default_plugins.update(PluginsConfigParser.from_config(entry['plugins']))
        default_plugins = default_plugins.to_args()

    if entry.get('baseline_file'):
        baseline_filename = entry['baseline_file']

    if entry.get('exclude_regex'):
        exclude_regex = entry['exclude_regex']

    repo_class = tracked_repo_factory(
        entry.get('is_local_repo', False),
        entry.get('s3_backend', False),
    )

    # TODO: Pass in s3_config_file
    return repo_class(
        repo=entry['repo'],
        sha=entry['sha'],
        cron=entry['cron'],
        plugins=default_plugins,
        base_temp_dir=base_temp_dir,
        baseline_filename=baseline_filename,
        exclude_regex=exclude_regex,
    )
