from detect_secrets_server.storage.file import FileStorageWithLocalGit
from detect_secrets_server.storage.s3 import S3Storage


def display_tracked_repositories(args):
    for repo, is_local in list_tracked_repositories(args):
        if is_local is None or args.local == is_local:
            print(repo['repo'])


def list_tracked_repositories(args):
    mapping = {
        's3': lambda args: S3Storage(args.root_dir, args.s3_config),

        # Using the local version, since the local version includes the non-local one.
        'file': lambda args: FileStorageWithLocalGit(args.root_dir),
    }

    return mapping[args.storage](args).get_tracked_repositories()
