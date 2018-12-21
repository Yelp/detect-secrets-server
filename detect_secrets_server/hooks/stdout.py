"""
Print to stdout.
"""
from __future__ import print_function

import json

from .base import BaseHook


class StdoutHook(BaseHook):

    def alert(self, repo_name, secrets):
        print(json.dumps({
            'repo': repo_name,
            'output': secrets,
        }))
