from __future__ import absolute_import
from __future__ import print_function

from detect_secrets_server.storage.file import FileStorageWithLocalGit
from detect_secrets_server.storage.s3 import S3Storage


def display_tracked_repositories(args):
    for repo, is_local in list_tracked_repositories(args):
        if args.local == is_local:
            print(repo['repo'])


def list_tracked_repositories(args):
    mapping = {
        's3': S3Storage,

        # Using the local version, since the local version includes the non-local one.
        'file': FileStorageWithLocalGit,
    }

    return mapping[args.storage](
        args.root_dir
    ).get_tracked_repositories()
