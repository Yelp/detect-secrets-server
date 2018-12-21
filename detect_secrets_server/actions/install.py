import tempfile

from crontab import CronTab

from .list import list_tracked_repositories


def install_mapper(args):
    mapping = {
        'cron': _install_cron,
    }

    mapping[args.method](args)


def _install_cron(args):
    # Get user's current crontab, so as not to override it
    old_content = []
    cron = CronTab(user=True)
    with tempfile.NamedTemporaryFile() as temp:
        cron.write(temp.name)

        # Ignore all previous entries
        for line in temp.readlines():
            line = line.decode()
            if line and 'detect-secrets-server' not in line:
                old_content.append(line.strip())

    # Create jobs from tracked repositories
    jobs = []
    for repo, is_local in list_tracked_repositories(args):
        jobs.append(
            '{}    detect-secrets-server scan {} {} {}'.format(
                repo['crontab'],
                repo['repo'],
                '--local' if is_local else '',
                args.output_hook_command,
            ).strip()
        )

    # Construct new crontab
    content = '\n'.join(jobs)
    if old_content:
        content = '{}\n\n{}'.format(
            '\n'.join(old_content),
            content,
        )

    cron = CronTab(
        tab=content,
        user=True,
    )
    cron.write_to_user(user=True)
