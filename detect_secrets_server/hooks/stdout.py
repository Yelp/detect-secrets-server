"""
Print to stdout.
"""
import json

from .base import BaseHook


class StdoutHook(BaseHook):

    def alert(self, repo_name, secrets):
        print(json.dumps({
            'repo': repo_name,
            'output': secrets,
        }))
