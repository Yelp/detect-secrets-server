#!/usr/bin/env python3.6
"""
This is an example bare-bone script that you can use as an argument for
setting up an output hook.

>>> $ detect-secrets-server --scan-repo yelp/detect-secrets
...     --output-hook examples/standalone_hook.py
"""
import json
import sys


def main():
    print('repo:', sys.argv[1])
    print(sys.argv[2])
    print(json.dumps(json.loads(sys.argv[2]), indent=2))


if __name__ == '__main__':
    main()
