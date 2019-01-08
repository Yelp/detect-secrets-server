"""
This provides a common interface to run arbitrary scripts, provided
by the `--output-hook` option.

The script you provide must be executable, and accept two command line
inputs:
    1. the name of the repository where secrets are found, and
    2. the json output of secrets found.
"""
import json
import os
import subprocess

from .base import BaseHook


class ExternalHook(BaseHook):

    def __init__(self, filename):
        if filename.startswith('/'):
            self.filename = filename
        else:
            self.filename = os.path.join(
                os.getcwd(),
                filename,
            )

    def alert(self, repo_name, secrets):
        subprocess.call([
            self.filename,
            repo_name,
            json.dumps(secrets),
        ])
