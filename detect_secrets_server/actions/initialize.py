import copy

from detect_secrets_server.repos import tracked_repo_factory


def initialize(args):
    """Initializes a list of repositories from a specified repos.yaml,
    and returns the commands to add to your crontab.

    Sets up local file storage for tracking repositories.
    """
    tracked_repos = _load_from_config(
        args.initialize,
        args.plugins,
        args.base_temp_dir,
        args.baseline,
        args.exclude_regex,
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
        default_plugins = _merge_plugins(entry['plugins'], default_plugins)

    if entry.get('baseline_file'):
        baseline_filename = [entry['baseline_file']]

    if entry.get('exclude_regex'):
        exclude_regex = [entry['exclude_regex']]

    repo_class = tracked_repo_factory(
        entry.get('is_local_repo', False),
        entry.get('s3_backend', False),
    )

    return repo_class(
        repo=entry['repo'],
        sha=entry['sha'],
        cron=entry['cron'],
        plugins=default_plugins,
        base_temp_dir=base_temp_dir[0],
        baseline_filename=baseline_filename[0],
        exclude_regex=exclude_regex[0],
    )


def _merge_plugins(plugins, default_plugins):
    """
    NOTE: As with detect_secrets.plugins.__init__.initialize_plugins, this
    assumes there is at most one initialization parameter. If upstream
    changes, this would also have to change.

    :type plugins: dict
    :param plugins: key,value pairs of plugins, to initialization values

    :type default_plugins: dict
    :param default_plugins: Example format:
        {
            'HexHighEntropyString': {
                'hex_limit': [3],
            },
        }

    :returns: combined plugins, in default_plugins style.
    """
    combined_plugins = copy.deepcopy(default_plugins)
    for plugin_name in plugins:
        if (plugins[plugin_name] is False or plugins[plugin_name] is None) and \
                plugin_name in default_plugins:
            del combined_plugins[plugin_name]
            continue

        key = list(default_plugins[plugin_name].keys())[0]
        combined_plugins[plugin_name][key] = [plugins[plugin_name]]

    return combined_plugins
