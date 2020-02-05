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


### v0.2.18
##### February 4th, 2020

#### :tada: New Features

* [Add ability to scan repo HEAD](https://github.com/Yelp/detect-secrets-server/commit/17e57e7ce3e60772cec96f3ad424d74684b3fdaf)


### v0.2.17
##### October 15th, 2019

#### :bug: Bugfixes

* Fixed a bug where our cron functionality didn't handle a custom root directory ([#36], thanks [@gsoyka])

[#36]: https://github.com/Yelp/detect-secrets-server/pull/36



### v0.2.16
##### October 2nd, 2019

#### :tada: New Features

* [Added handling of local bare repos](https://github.com/Yelp/detect-secrets-server/commit/99d4a1e384c07a77a2d32fd9febe8c897d94c922)



### v0.2.15
##### September 30th, 2019

#### :bug: Bugfixes

* Fixed a bug where we were would crash with a `OSError: [Errno 7] Argument list too long` if there were too many files in the git diff ([#35])

[#35]: https://github.com/Yelp/detect-secrets-server/pull/35



### v0.2.14
##### September 19th, 2019

#### :tada: New Features

* Added an `--always-run-output-hook` flag ([#34], thanks [@mindfunk])

#### :bug: Bugfixes

* [Fixed a bug where we were never skipping ignored file extensions](https://github.com/Yelp/detect-secrets-server/commit/1c0d5120b979d68f357eb473bf476a66b4899ce9)

[#34]: https://github.com/Yelp/detect-secrets-server/pull/34



### v0.2.13
##### September 16th, 2019

#### :snake: Miscellaneous

- Bumped the detect-secrets from version [`v0.12.2`](https://github.com/Yelp/detect-secrets/blob/master/CHANGELOG.md#v0122)  to [`v0.12.6`](https://github.com/Yelp/detect-secrets/blob/master/CHANGELOG.md#v0126)



### v0.2.12
##### June 4th, 2019

#### :bug: Bugfixes

* Fixed a **very important bug** where we were not fetching changes for non-local repositories ([#30], thanks [@chetmancini], [@akshayatplivo], [@ajchida], [@rameshkumar-a]))
* [Fixed a `UnidiffParseError: Hunk is shorter than expected` crash](https://github.com/Yelp/detect-secrets-server/pull/30/commits/bc0170045e3778446c0d68fb19b0dc58543602c2)

#### :art: Display Changes

* [Added a helpful error message for when a user tries to use S3 features without boto3 installed](https://github.com/Yelp/detect-secrets-server/commit/15525d4eb35dcd1b79e458cdf360ab9f5a77957c)

[#30]: https://github.com/Yelp/detect-secrets-server/pull/30
[@chetmancini]: https://github.com/chetmancini
[@akshayatplivo]: https://github.com/akshayatplivo
[@ajchida]: https://github.com/ajchida
[@rameshkumar-a]: https://github.com/rameshkumar-a



### v0.2.11
##### March 21st, 2019

#### :tada: New Features

* [Bumped version of `detect-secrets`](https://github.com/Yelp/detect-secrets-server/commit/bfe7295b3681f0fe9d6d4652fa9437aab5e2e664) from [`v0.12.0`](https://github.com/Yelp/detect-secrets/blob/master/CHANGELOG.md#v0120) to [v0.12.2](https://github.com/Yelp/detect-secrets/blob/master/CHANGELOG.md#v0122), primarily to improve performance



### v0.2.10
##### March 14th, 2019

#### :bug: Bugfixes

* Fixed a bug where we were not assigning the commit of found secrets to HEAD ([#27])

[#27]: https://github.com/Yelp/detect-secrets-server/pull/27



### v0.2.9
##### March 14th, 2019

#### :snake: Miscellaneous

* [Fixed](https://github.com/Yelp/detect-secrets-server/commit/472ba87ecc220be96f10477914b09da159d9bc04) an [internal issue](https://github.com/Yelp/venv-update)



### v0.2.8
##### March 14th, 2019

#### :bug: Bugfixes

* Fixed a bug where we were `git fetch`ing for local git repositories ([#26])

[#26]: https://github.com/Yelp/detect-secrets-server/pull/26



### v0.2.7
##### March 13th, 2019

#### :tada: New Features

* Added a `--diff-filter` optimization, so we only scan added, copied or modified files ([#22])

[#22]: https://github.com/Yelp/detect-secrets-server/pull/22

#### :bug: Bugfixes

* Fixed a bug where, `scan` on bare repositories gave a `Your local changes to the following files would be overwritten by merge:` error ([#23])

[#23]: https://github.com/Yelp/detect-secrets-server/pull/23



### v0.2.6
##### February 12th, 2019

#### :bug: Bugfixes

* [Fixed a bug where we were using an older version of `detect-secrets` in our `requirements-dev` `txt` files](https://github.com/Yelp/detect-secrets-server/commit/0ff9f095167e5090a8ebba1ddc4e7317b3c23800)



### v0.2.5
##### February 12th, 2019

#### :tada: New Features

* Added `--exclude-files` and `--exclude-lines` args to scan ([#18])
* Added git commit to secrets before calling `output_hook.alert` ([#15])

[#15]: https://github.com/Yelp/detect-secrets-server/pull/15

#### :boom: Breaking Changes

* Started to ignore the `exclude_regex` in repo metadata when scanning as a short-term solution for [Issue 17](https://github.com/Yelp/detect-secrets-server/issues/17) ([#18])

[#18]: https://github.com/Yelp/detect-secrets-server/pull/18



### v0.2.4
##### January 14th, 2019

#### :bug: Bugfixes

* `add` and `scan` now handle non-SSH urls for git cloning. See
  [Issue 13](https://github.com/Yelp/detect-secrets-server/issues/13) for more details.



### v0.2.2
##### January 11th, 2019

#### :tada: New Features

* Bumped version of `detect-secrets` to 0.11.4, so that we can leverage the
  new `AWSKeyDetector` and the `KeywordDetector`.



### v0.2.1
##### January 10th, 2019

#### :tada: New Features

* Added support for delegating state management to output hooks, using the
  flag `--always-update-state`.



### v0.2.0
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



# Special thanks to our awesome contributors! :clap:

- [@gsoyka]
- [@mindfunk]

[@gsoyka]: https://github.com/gsoyka
[@mindfunk]: https://github.com/mindfunk
