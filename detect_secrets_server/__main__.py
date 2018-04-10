from __future__ import absolute_import
from __future__ import print_function

import codecs
import sys

import yaml
from detect_secrets.core.log import CustomLog

from detect_secrets_server import actions
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

    if args.initialize:
        output = actions.initialize(args)
        if output:
            print(output)

    elif args.add_repo:
        actions.add_repo(args)

    elif args.scan_repo:
        return actions.scan_repo(args)

    return 0


if __name__ == '__main__':
    sys.exit(main())
