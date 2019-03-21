from __future__ import absolute_import

import json as json_module

from detect_secrets.core.potential_secret import PotentialSecret
from detect_secrets.core.secrets_collection import SecretsCollection


def metadata_factory(repo, json=False, **kwargs):
    """
    This generates a layout you would expect for metadata storage with files.

    :type json: bool
    :param json: if True, will return string instead.
    """
    output = {
        "baseline_filename": None,
        "crontab": "0 0 * * *",
        "exclude_regex": None,
        "plugins": {
            "AWSKeyDetector": {},
            "Base64HighEntropyString": {
                "base64_limit": 4.5,
            },
            "BasicAuthDetector": {},
            "HexHighEntropyString": {
                "hex_limit": 3,
            },
            "KeywordDetector": {
                'keyword_exclude': None
            },
            "PrivateKeyDetector": {},
            "SlackDetector": {}
        },
        "repo": repo,
        "sha": 'sha256-hash',
    }

    output.update(kwargs)

    if json:
        return json_module.dumps(output, indent=2, sort_keys=True)
    return output


def single_repo_config_factory(repo, **kwargs):
    """
    This generates a layout used in passing config files when initializing repos.
    """
    output = {
        'repo': repo,
    }
    output.update(kwargs)

    return output


def potential_secret_factory(type_='type', filename='filename', lineno=1, secret='secret'):
    """This is only marginally better than creating PotentialSecret objects directly,
    because of default values.
    """
    return PotentialSecret(
        typ=type_,
        filename=filename,
        lineno=lineno,
        secret=secret,
    )


def secrets_collection_factory(secrets=None, plugins=(), exclude_regex=''):  # pragma: no cover
    """
    :type secrets: list(dict)
    :param secrets: list of params to pass to add_secret.
                    Eg. [ {'secret': 'blah'}, ]

    :type plugins: tuple
    :type exclude_regex: str

    :rtype: SecretsCollection
    """
    collection = SecretsCollection(plugins, exclude_regex)

    if plugins:
        collection.plugins = plugins

    # Handle secrets
    if secrets is None:
        return collection

    for kwargs in secrets:
        _add_secret(collection, **kwargs)

    return collection


def _add_secret(collection, type_='type', secret='secret', filename='filename', lineno=1):
    """Utility function to add individual secrets to a SecretCollection.

    :param collection: SecretCollection; will be modified by this function.
    :param filename:   string
    :param secret:     string; secret to add
    :param lineno:     integer; line number of occurring secret
    """
    if filename not in collection.data:  # pragma: no cover
        collection[filename] = {}

    tmp_secret = potential_secret_factory(
        type_=type_,
        filename=filename,
        lineno=lineno,
        secret=secret,
    )
    collection.data[filename][tmp_secret] = tmp_secret
