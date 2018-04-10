from detect_secrets_server.plugins import PluginsConfigParser
from detect_secrets_server.repos import tracked_repo_factory
from detect_secrets_server.repos.base_tracked_repo import OverrideLevel


def initialize(args):
    """Initializes a list of repositories from a specified repos.yaml,
    and returns the commands to add to your crontab.

    Sets up local file storage for tracking repositories.
    """
    tracked_repos = _load_from_config(
        args.initialize,
        args.plugins,
        args.base_temp_dir[0],
        args.baseline[0],
        args.exclude_regex[0],
    )

    cron_repos = [repo for repo in tracked_repos if repo.save()]
    if not cron_repos:
        return

    output = '# detect-secrets scanner'
    for repo in cron_repos:
        output += '\n{} {}'.format(
            repo.cron(),
            args.output_hook_command,
        )

    return output


def add_repo(args):
    """Sets up an individual repository for tracking."""
    repo_class = tracked_repo_factory(
        args.local,
        bool(args.s3_config_file),
    )

    # TODO: Pass in s3_config_file
    repo = repo_class(
        repo=args.add_repo[0],

        # Will be updated to HEAD upon first update
        sha='',

        # TODO: Comment
        cron='',

        plugins=args.plugins,
        base_temp_dir=args.base_temp_dir[0],
        baseline_filename=args.baseline[0],
        exclude_regex=args.exclude_regex[0],
    )

    # Clone repo, if needed.
    repo.clone_and_pull_repo()

    # Make the last_commit_hash of repo point to HEAD
    repo.update()

    # Save the last_commit_hash, if we have nothing on file already
    repo.save(OverrideLevel.NEVER)


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
            _initialize_repo(
                entry,
                default_plugins,
                base_temp_dir,
                baseline_filename,
                exclude_regex,
            )
        )

    return output


def _initialize_repo(
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
