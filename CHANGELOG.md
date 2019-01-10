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

[#xxxx]: https://github.com/Yelp/detect-secrets/pull/xxxx
[@xxxx]: https://github.com/xxxx
-->

### 0.2.1

##### Jan 10, 2019

* Added support for delegating state management to output hooks, using the
  flag `--always-update-state`.

### 0.2.0

##### Jan 09, 2019

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
