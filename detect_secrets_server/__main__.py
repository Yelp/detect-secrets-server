from __future__ import absolute_import
from __future__ import print_function

import sys

from detect_secrets.core.log import log

from detect_secrets_server import actions
from detect_secrets_server.core.usage.parser import ServerParserBuilder


def parse_args(argv):
    return ServerParserBuilder().parse_args(argv)


def main(argv=None):
    """
    Expected Usage:
      1. Initialize TrackedRepos, and save to crontab.
      2. Each cron command will run and scan git diff from previous commit saved, to now.
      3. If something is found, alert.

    :return: shell error code
    """
    if not argv:
        argv = sys.argv[1:]

    if len(argv) == 1:  # pragma: no cover
        argv.append('-h')

    args = parse_args(argv)
    if args.verbose:    # pragma: no cover
        log.set_debug_level(args.verbose)

    if args.action == 'add':
        if getattr(args, 'config', False):
            output = actions.initialize(args)
            if output:
                print(output)
        else:
            actions.add_repo(args)

    elif args.action == 'scan':
        return actions.scan_repo(args)

    return 0


if __name__ == '__main__':
    sys.exit(main())
