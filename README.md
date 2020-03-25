[![Build Status](https://travis-ci.org/Yelp/detect-secrets-server.svg?branch=master)](https://travis-ci.org/Yelp/detect-secrets-server)
[![PyPI version](https://badge.fury.io/py/detect-secrets-server.svg)](https://badge.fury.io/py/detect-secrets-server)

# detect-secrets-server

## About

`detect-secrets-server` is the server-side counterpart to [`detect-secrets`](
https://github.com/Yelp/detect-secrets), that can be used to detect secrets retroactively.
While `detect-secrets` is a fantastic tool to self-identify secrets in your codebase and
prevent them from entering, it is ultimately a client-side protection and can be easily
bypassed.

Adding a
[pre-receive hook](https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks#_code_pre_receive_code)
would also fail to be effective, due to the nuanced nature of `detect-secrets`.
If you're preventing any potential secrets at a commit level, you may block developers
due to false positives.

Therefore, `detect-secrets-server` accomplishes several things:

1. **Tracks** multiple repositories and maintains its own state of known secrets,
2. Periodically **scans** tracked repositories for any new incoming secrets, and
3. Sends **alerts** when it finds secrets in new commits.

## Example Usage

### Quick Start

```
$ pip install detect-secrets-server[cron]
$ detect-secrets-server add git@github.com:yelp/detect-secrets
$ detect-secrets-server install cron
```

This will add `detect-secrets` as a tracked repository, and install it to the
current user's crontab so that it will periodically scan for updates.

### Manually Scanning a Repository

Once you have a tracked repository, you can scan it as follows:

```
$ detect-secrets-server scan yelp/detect-secrets
```

### Adding a Local Repository

Instead of having `detect-secrets-server` clone git repositories on your behalf, you can
have it point to locally managed repositories. This is especially handy when testing
`detect-secrets-server`.

```
~/pg/detect-secrets-server $ detect-secrets-server add ../detect-secrets --local
~/pg/detect-secrets-server $ cd ../detect-secrets
~/pg/detect-secrets $ echo "'$(echo "asdf" | shasum -a 256 | cut -d ' ' -f 1)'" >> detect_secrets/pre_commit_hook.py
~/pg/detect-secrets $ git add -u; git commit -m 'test'; cd ../detect-secrets-server
~/pg/detect-secrets-server $ detect-secrets-server scan ../detect-secrets --local
```

### Adding Multiple Repositories at Once

To track multiple repositories at once, you can specify a config file when adding tracked
repositories.

```
$ detect-secrets-server add examples/repos.yaml --config
```

The following keys are accepted in this config file:

```
repos.yaml
  |- tracked		# This is a list of repositories that will be tracked
```

Tracked repository options are as follows:

| attribute      | description
| -------------- | -----------
| repo           | git URL or local file path to clone (**required**).
| crontab        | [crontab syntax](https://crontab.guru/) of how often to run a scan for this repo.
| sha            | The commit hash to start scanning from. If not provided, will use HEAD.
| storage        | Either one of the following: (`file`, `s3`). Determines where to store metadata. Defaults to `file`.
| is\_local\_repo| True/False depending on if the repo is already on the filesystem. Defaults to False.
| plugins        | Individual repository plugin settings, to override default values.
| baseline       | The filename to parse the detect-secrets baseline from.
| exclude\_regex | Per repo regex for excluding files from scan.

Be sure to check out `examples/repos.yaml` for an reference.

## Configuration Options

### Plugins Options

There are several ways to manage the various `detect-secrets` plugins for your
individual tracked repositories.

By default, all repositories will inherit the default values as prescribed by
`detect-secrets`. These can be overridden with the same CLI flags as you would
for `detect-secrets` (e.g. `--hex-limit 5`, `--no-private-key-scan`).

If you choose to use a config file to add multiple repositories at once, you can
specify all the plugins' options that you want to customize under the `plugins`
key. Each key is the **name** of the plugin, and its values are the keyword
arguments that it accepts.

Note that any plugin not explicitly mentioned will use default values. If you
explicitly want to disable a given plugin for a given repository, simply set its
value to `False`.

For example, in `examples/repos.yaml`, we have the following plugin configuration:

```
plugins:
    Base64HighEntropyString:
        base64_limit: 4
    PrivateKeyDetector: False
```

This will initialize plugins as follows:

* Base64HighEntropyString: 4    (explicitly set)
* BasicAuthDetector: enabled    (enabled by default)
* HexHighEntropyString: 3       (default limits)
* PrivateKeyDetector: disabled  (explicitly disabled)

### Storage Options

`detect-secrets-server` stores state through metadata it keeps for the repositories
it tracks. You can configure a variety of different storage options for this using
the `--storage` option, including:

#### file

The most basic version is file-based storage. Metadata is stored in a directory structure
under your configured root directory (`--root-dir`, defaults to `~/.detect-secrets-server`).

#### s3

If you want to store metadata as files in Amazon S3, you can do so too. Be sure to pip install
the `boto3` library, and specify the additional S3 config options necessary.

```
s3 storage settings:
  Configure options for using Amazon S3 as a storage option.

  --s3-credentials-file FILENAME
                        Specify keys for storing files on S3.
  --s3-bucket BUCKET_NAME
                        Specify which bucket to perform S3 operations on.
  --s3-prefix PREFIX    Specify the path prefix within the S3 bucket.
  --s3-config CONFIG_FILE
                        Specify config file for all S3 config options.
```

You can also specify a config file instead, with `--s3-config`. For example, the following
invocations are equivalent:

```
$ detect-secrets-server add git@github.com:yelp/detect-secrets --storage s3 \
	--s3-credentials-file examples/aws_credentials.json \
	--s3-bucket my-bucket-in-us-east-1 \
	--s3-prefix secret_detector/tracked_repos
```

and

```
$ detect-secrets-server add git@github.com:yelp/detect-secrets --storage s3 \
	--s3-config examples/s3.yaml
```

### Alerting Options

You are able to configure `detect-secrets-server` to alert you through a variety of ways
when it detects a secret. These include:

#### Adhoc Script

When you specify an executable file with `--output-hook`, this file will run upon secret
detection. Using `examples/standalone_hook.py` as an example, the output would look
something like:

```
repo: yelp/detect-secrets
{
    "detect_secrets/pre_commit_hook.py": [
        {
            "author": "aaronloo",
            "hashed_secret": "7cec71eb6b597e71690378dfb169169a283f2e94",
            "line_number": 1,
            "type": "Hex High Entropy String"
        }
    ]
}
```

#### pysensu

We support
[PySensu alerting](http://pysensu-yelp.readthedocs.io/en/latest/#pysensu_yelp.send_event)
as well, so check out those docs if you want to configure your Sensu alerts.

You can invoke this like the following:

```
$ detect-secrets-server scan yelp/detect-secrets \
	--output-hook pysensu \
	--output-config examples/pysensu.config.yaml
```
