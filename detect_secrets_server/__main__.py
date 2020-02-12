import sys

from detect_secrets.core.log import log

from detect_secrets_server import actions
from detect_secrets_server.core.usage.parser import ServerParserBuilder


def parse_args(argv):
    return ServerParserBuilder().parse_args(argv)


def main(argv=None):
    if argv is None:    # pragma: no cover
        argv = sys.argv[1:]

    if len(argv) == 0:  # pragma: no cover
        argv.append('-h')

    args = parse_args(argv)
    if args.verbose:    # pragma: no cover
        log.set_debug_level(args.verbose)

    if args.action == 'add':
        if getattr(args, 'config', False):
            actions.initialize(args)
        else:
            actions.add_repo(args)

    elif args.action == 'install':
        actions.install_mapper(args)

    elif args.action == 'list':
        actions.display_tracked_repositories(args)

    elif args.action == 'scan':
        return actions.scan_repo(args)

    return 0


if __name__ == '__main__':
    sys.exit(main())
