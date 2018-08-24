# detect-secrets-server

## About

`detect-secrets-server` is the server-side counterpart to [`detect-secrets`](https://github.com/Yelp/detect-secrets), that can be used to detect secrets retroactively. It currently is only compatible with [version `0.8.8`](https://github.com/Yelp/detect-secrets/blob/master/CHANGELOG.md#090) of [`detect-secrets`](https://github.com/Yelp/detect-secrets)


### Server-side Secret Scanning

There are several steps to setting up your server, to allow for customizability
dependent on the requirements of your existing system.

1. Installing the Server Tool
2. Setting up Default Settings (**optional**)
3. Specifying Tracked Repositories
4. Hooking Up an Alerting System
5. Installing Crontabs

#### 1. Installing the Server Tool

```
$ pip install detect-secrets-server
```

#### 2. Setting Up Default Settings

The following keys are accepted in your config file:

```
config.yaml
  |- default		# These are default values to use for each tracked repo.
```

The following attributes are supported under the `default` namespace, and set
default settings for all repositories scanned with the `detect-secrets-server`
tool.

All attributes are **optional**, and can be overriden in `repos.yaml`.

| attribute      | description
| -------------- | -----------
| base\_tmp\_dir | Local path used for cloning repositories, and storing tracked metadata.
| baseline       | Filename to parse the detect-secrets baseline from.
| exclude\_regex | Files to ignore, when scanning files for secrets.
| plugins        | List of plugins, with their respective settings. Currently, these take precedence over values set via command line.

See the sample `config.yaml.sample` for an example.

#### 3. Specifying Tracked Repositories

All tracked repositories need to be defined in `repos.yaml`.
See `repos.yaml.sample` for an example.

The following attributes are supported:

| attribute       | description
| --------------- | -----------
| repo            | Where to `git clone` the repo from (**required**)
| is\_local\_repo | True or False depending on if the repo is already on the filesystem (**required**)
| sha             | The commit hash to start scanning from (**required**)
| baseline        | The filename to parse the detect-secrets baseline from
| cron            | [crontab syntax](https://crontab.guru/) of how often to run a scan for this repo
| plugins         | List of plugins, with their respective settings. This takes precedence over both `config.yaml` settings, and command line arguments.

#### 4. Hooking Up an Alerting System

Currently, we only support [PySensu
alerting](http://pysensu-yelp.readthedocs.io/en/latest/#pysensu_yelp.send_event),
so check out those docs on configuring your Sensu alerts.

See the sample `.pysensu.config.yaml.sample` for an example, but be sure to
name your file `.pysensu.config.yaml`.

#### 5. Installing Crontabs

```
echo -e "$(crontab -l)\n\n$(detect-secrets-server --initialize)" | crontab -
```
