"""
This provides a common interface to run arbitrary scripts, provided
by the `--output-hook` option.

The script you provide must be executable, and accept two command line
inputs:
    1. the name of the repository where secrets are found, and
    2. the json output of secrets found.
"""
import json
import subprocess

from .base import BaseHook


class ExternalHook(BaseHook):

    def __init__(self, filename):
        self.filename = filename

    def alert(self, repo_name, secrets):
        subprocess.call([
            self.filename,
            repo_name,
            json.dumps(secrets),
        ])
