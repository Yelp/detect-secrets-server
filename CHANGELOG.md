# What's New

Thanks to all our contributors, users, and the many people that make
`detect-secrets-server` possible! :heart:

If you love `detect-secrets-server`, please star our project on GitHub to show
your support! :star:

<!--
### A.B.C
##### MMM DD, YYYY

#### :newspaper: News
#### :mega: Release Highlights
#### :boom: Breaking Changes
#### :tada: New Features
#### :sparkles: Usability
#### :mortar_board: Walkthrough / Help
#### :performing_arts: Performance
#### :telescope: Precision
#### :bug: Bugfixes
#### :snake: Miscellaneous

[#xxxx]: https://github.com/Yelp/detect-secrets-server/pull/xxxx
[@xxxx]: https://github.com/xxxx
-->

### 0.2.7

##### March 13th, 2019

#### :tada: New Features

* Added a `--diff-filter` optimization, so we only scan added, copied or modified files ([#22])

[#22]: https://github.com/Yelp/detect-secrets-server/pull/22

#### :bug: Bugfixes

* Fixed a bug where, `scan` on bare repositories gave a `Your local changes to the following files would be overwritten by merge:` error ([#23])

[#23]: https://github.com/Yelp/detect-secrets-server/pull/23


### 0.2.6

##### February 12th, 2019

#### :bug: Bugfixes

* [Fixed a bug where we were using an older version of `detect-secrets` in our `requirements-dev` `txt` files](https://github.com/Yelp/detect-secrets-server/commit/0ff9f095167e5090a8ebba1ddc4e7317b3c23800)


### 0.2.5

##### February 12th, 2019

#### :tada: New Features

* Added `--exclude-files` and `--exclude-lines` args to scan ([#18])
* Added git commit to secrets before calling `output_hook.alert` ([#15])

[#15]: https://github.com/Yelp/detect-secrets-server/pull/15

#### :boom: Breaking Changes

* Started to ignore the `exclude_regex` in repo metadata when scanning as a short-term solution for [Issue 17](https://github.com/Yelp/detect-secrets-server/issues/17) ([#18])

[#18]: https://github.com/Yelp/detect-secrets-server/pull/18


### 0.2.4

##### January 14th, 2019

#### :bug: Bugfixes

* `add` and `scan` now handle non-SSH urls for git cloning. See
  [Issue 13](https://github.com/Yelp/detect-secrets-server/issues/13) for more details.


### 0.2.2

##### January 11th, 2019

* Bumped version of `detect-secrets` to 0.11.4, so that we can leverage the
  new `AWSKeyDetector` and the `KeywordDetector`.


### 0.2.1

##### January 10th, 2019

* Added support for delegating state management to output hooks, using the
  flag `--always-update-state`.


### 0.2.0

##### January 09th, 2019

#### :boom: Breaking Changes

* All previous config files' format has been changed, for better usability
  (and reducing the need to supply multiple config files during a single
  invocation). Be sure to check out some examples in
  [examples/](https://github.com/Yelp/detect-secrets-server/tree/master/examples)

* The CLI API has also been changed, to support better usability. Check out
  how to use the new commands with `-h`.

#### :tada: New Features

* **Actually** works with the latest version of `detect-secrets`.

* New `--output-hook` functionality, to specify arbitrary scripts for handling
  alerts. This should make it easier, so users aren't forced into using pysensu.

* `detect-secrets-server list` supports a convenient way to list all tracked
  repositories.

* `detect-secrets-server install` is a modular way to connect tracked repositories
  with a system that runs `detect-secrets-server scan` on a regular basis.
  Currently, the only supported method is `cron`.

#### :mega: Release Highlights

* Minimal dependencies! Previously, you had to install boto3, even if you weren't
  using the S3 storage option. Now, only install what you need, based on your
  unique setup.

* Introduction of the `Storage` class abstraction. This separates the management
  of tracked repositories (git cloning, baseline comparisons) with the method of
  storing server metadata, for cleaner code, decoupled architecture, and
  modularity.
