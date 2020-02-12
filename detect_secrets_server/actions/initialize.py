from detect_secrets_server.repos.base_tracked_repo import OverrideLevel
from detect_secrets_server.repos.factory import tracked_repo_factory


def add_repo(args):
    """Sets up an individual repository for tracking."""
    repo = _create_single_tracked_repo(
        repo=args.repo,

        # Will be updated to HEAD upon first update
        sha='',

        crontab=args.crontab,
        plugins=args.plugins,
        rootdir=args.root_dir,
        baseline_filename=args.baseline,
        exclude_regex=args.exclude_regex,

        is_local=args.local,
        s3_config=args.s3_config if args.storage == 's3' else None,
    )

    _clone_and_save_repo(repo)


def initialize(args):
    """Initializes a list of repositories from a specified repos.yaml,
    and returns the commands to add to your crontab.

    Sets up local file storage for tracking repositories.
    """
    tracked_repos = [
        _create_single_tracked_repo(
            repo=repo['repo'],
            crontab=repo['crontab'],
            sha=repo['sha'],
            plugins=repo['plugins'],
            baseline_filename=repo['baseline'],
            exclude_regex=repo['exclude_regex'],

            is_local=repo.get('is_local_repo', False),
            s3_config=args.s3_config if repo['storage'] == 's3' else None,

            rootdir=args.root_dir,
        )
        for repo in args.repo
    ]

    for repo in tracked_repos:
        _clone_and_save_repo(repo)


def _create_single_tracked_repo(
    repo,
    sha,
    crontab,
    plugins,
    rootdir,
    baseline_filename,
    exclude_regex,
    is_local,
    s3_config,
):
    """
    These are REQUIRED arguments:
        :type repo: str
        :param repo: The url to clone, in `git clone <url>`

        :type sha: str
        :param sha: Last commit hash scanned

        :type crontab: str
        :param crontab: crontab syntax, denoting frequency of repo scan

    These arguments can have global defaults:
        :type plugins: dict
        :param plugins: mapping of plugin classnames to initialization values

        :type baseline_filename: str
        :param baseline_filename: repo-specific filename of baseline file

    Optional arguments include:
        :type rootdir: str
        :param rootdir: location of where you want to clone the repo for
            local storage

        :type exclude_regex: str
        :param exclude_regex: filenames that match this regex will be excluded from
            scanning.

        :type is_local: bool
        :param is_local: indicates that repository is locally stored (no need to
            git clone)

        :type s3_config: dict
        :param s3_config: files generated to save state will be synced with Amazon S3.
    """
    repo_class = tracked_repo_factory(
        is_local,
        bool(s3_config),
    )

    return repo_class(
        repo=repo,
        sha=sha,
        crontab=crontab,

        plugins=plugins,
        rootdir=rootdir,
        baseline_filename=baseline_filename,
        exclude_regex=exclude_regex,

        s3_config=s3_config,
    )


def _clone_and_save_repo(repo):
    """
    :type repo: BaseTrackedRepo
    :param repo: repo to clone (if appropriate) and save
    """
    # Clone repo, if needed.
    repo.storage.clone()

    # Make the last_commit_hash of repo point to HEAD
    if not repo.last_commit_hash:
        repo.update()
        return repo.save(OverrideLevel.ALWAYS)

    # Save the last_commit_hash, if we have nothing on file already
    return repo.save(OverrideLevel.NEVER)
