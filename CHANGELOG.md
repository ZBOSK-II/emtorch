# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
 - better console log filtering when not in `--verbose` mode


## [3.0.0] - 2026-06-22

### Changed
 - dropped Python 3.13 support
 - support for "plugins" - subtasks can be registered as "entry-points"
 - internal refactoring: all tasks now rely on asyncio, no more manual "workers" etc
 - configuration now based on TOML format
 - case instances identifiers will start from 1 and not 0.
 - "git style" subcommands introduced, with built-in help


## [2.1.2] - 2026-06-01

### Changed
 - Unknown SSH keys will be only logged - simplifies integration with docker


## [2.1.1] - 2026-06-01

### Fixed
 - Version detection during build (proper PyPI packages marking)


## [2.1.0] - 2026-06-01

### Fixed
 - proper closing of streams in I/O event loop

### Changed
 - renamed results "keys" to "identifiers" internally
 - `EMTORCH_CASE_KEY` renamed to `EMTORCH_CASE_ID`
 - "groups" in results JSON became "subtasks" for consistency
 - `"all"` and `"cases"` inside results JSON embedded into `"cases"` to be more clear
 - entries in log will have consistent format for "subtask" name portion of the log
 - added `values` to results (possibility to aggregate values per case)
 - added `logger-int-matcher` and `logger-float-matcher` monitoring subtasks
 - added `file-write` subtask

### Added
 - `--repeats` argument will allow to repeat test cases for each data specified number of times
 - `--repeat-mode` argument will allow to select order of repetition (abc * 2 -> aabbcc or abcabc)
 - `EMTORCH_DATA_PATH` environment variable added to $-strings templates (contains path to current case data)
 - `EMTORCH_DATA_FILENAME` environment variable added to $-strings templates  (contains file name of the current case data)
 - `sftp-download` and `sftp-upload` subtasks for SFTP operations
 - `file-write` for writing to files

### Dependencies updated
 - mypy bump from 1.20.1 to 2.1.0 [\#53](https://github.com/ZBOSK-II/emtorch/pull/53) [\#55](https://github.com/ZBOSK-II/emtorch/pull/55) [\#59](https://github.com/ZBOSK-II/emtorch/pull/59) ([dependabot](https://github.com/dependabot))
 - types-paramiko bump from 4.0.0.20260408 to 4.0.0.20260518 [\#56](https://github.com/ZBOSK-II/emtorch/pull/56) [\#60](https://github.com/ZBOSK-II/emtorch/pull/60) ([dependabot](https://github.com/dependabot))
 - black bump from 26.3.1 to 26.5.1 [\#62](https://github.com/ZBOSK-II/emtorch/pull/62) ([dependabot](https://github.com/dependabot))
 - paramiko bump from 3.5.1 to 5.0.0


## [2.0.0] - 2026-04-13

### Changed

 - renamed project to emtorch


## [1.3.0] - 2026-04-13

**FINAL RELEASE** of the emfuzzer project. Further development performed as [emtorch](https://pypi.org/project/emtorch/).

### Changed
 - BREAKING CHANGE: Moving away from "injection" towards more generic usage of the project - "actions" introduced. Instead of a single dedicated tool to be executed after monitoring has started, set of "subtasks" called "actions" will execute. [\#28](https://github.com/ZBOSK-II/emtorch/pull/28) ([hcorg](https://github.com/hcorg))

### Dependencies updated
 - mypy bump from 1.19.1 to 1.20.1 [\#39](https://github.com/ZBOSK-II/emtorch/pull/39) [\#42](https://github.com/ZBOSK-II/emtorch/pull/42) ([dependabot](https://github.com/dependabot))
 - types-paramiko bump from 4.0.0.20260322 to 4.0.0.20260408 [\#38](https://github.com/ZBOSK-II/emtorch/pull/38) [\#42](https://github.com/ZBOSK-II/emtorch/pull/42) ([dependabot](https://github.com/dependabot))
 - cryptography bump from 46.0.5 to 46.0.7 [\#40](https://github.com/ZBOSK-II/emtorch/pull/40) [\#45](https://github.com/ZBOSK-II/emtorch/pull/45) ([dependabot](https://github.com/dependabot))
 - pygments bump from 2.19.2 to 2.20.0 [\#41](https://github.com/ZBOSK-II/emtorch/pull/41) ([dependabot](https://github.com/dependabot))
 - pytest bump from 9.0.2 to 9.0.3 [\#43](https://github.com/ZBOSK-II/emtorch/pull/43) ([dependabot](https://github.com/dependabot))


## [1.2.0] - 2026-03-16

### Changed

 - SSH will require prior key acceptance using system "known hosts" file [\#26](https://github.com/ZBOSK-II/emtorch/pull/26) ([hcorg](https://github.com/hcorg))

### Dependencies updated

 - isort bump from 6.1.0 to 8.0.1 [\#6](https://github.com/ZBOSK-II/emtorch/pull/6) [\#19](https://github.com/ZBOSK-II/emtorch/pull/19) ([dependabot](https://github.com/dependabot))
 - mypy bump from 1.16.0 to 1.19.1 [\#7](https://github.com/ZBOSK-II/emtorch/pull/7) [\#12](https://github.com/ZBOSK-II/emtorch/pull/12) ([dependabot](https://github.com/dependabot))
 - black bump from 25.1.0 to 26.3.1 [\#8](https://github.com/ZBOSK-II/emtorch/pull/8) [\#10](https://github.com/ZBOSK-II/emtorch/pull/10) [\#16](https://github.com/ZBOSK-II/emtorch/pull/16) [\#21](https://github.com/ZBOSK-II/emtorch/pull/21) [\#22](https://github.com/ZBOSK-II/emtorch/pull/22) ([dependabot](https://github.com/dependabot))
 - types-paramiko bump from 3.5.0.20250516 to 4.0.0.20250822 [\#9](https://github.com/ZBOSK-II/emtorch/pull/9) ([dependabot](https://github.com/dependabot))
 - pytest bump from 9.0.1 to 9.0.2 [\#11](https://github.com/ZBOSK-II/emtorch/pull/11) ([dependabot](https://github.com/dependabot))
 - pylint bump from 4.0.4 to 4.0.5 [\#18](https://github.com/ZBOSK-II/emtorch/pull/18) ([dependabot](https://github.com/dependabot))


## [1.1.0] - 2025-12-02

### Added

 - Support for Python 3.14 in GitHub Actions and PyPI packages.

### Changed

 - isort bump from 6.0.1 to 6.1.0 [\#3](https://github.com/ZBOSK-II/emtorch/pull/3) ([dependabot](https://github.com/dependabot))
 - pytest bump from 8.3.5 to 9.0.1 [\#5](https://github.com/ZBOSK-II/emtorch/pull/5) ([dependabot](https://github.com/dependabot))
 - pylint bump from 3.3.7 to 4.0.4 [\#2](https://github.com/ZBOSK-II/emtorch/pull/2) ([dependabot](https://github.com/dependabot))
 - flake8-pyproject bump from 1.2.3 to 1.2.4 [\#1](https://github.com/ZBOSK-II/emtorch/pull/1) ([dependabot](https://github.com/dependabot))
 - flake8 bump from 7.2.0 to 7.3.0 [\#4](https://github.com/ZBOSK-II/emtorch/pull/4) ([dependabot](https://github.com/dependabot))


## [1.0.0] - 2025-06-30

### Changed

 - Docker image now contains only emfuzzer (dropped CoAP experiment dependencies)

### Removed

 - CoAP experiment specific files


## [0.1.0] - 2025-06-16

Initial release to setup PyPI.

Fully functional emfuzzer - see README.md for details

[Unreleased]: https://github.com/ZBOSK-II/emtorch/compare/3.0.0...Unreleased
[3.0.0]: https://github.com/ZBOSK-II/emtorch/compare/2.1.2...3.0.0
[2.1.2]: https://github.com/ZBOSK-II/emtorch/compare/2.1.1...2.1.2
[2.1.1]: https://github.com/ZBOSK-II/emtorch/compare/2.1.0...2.1.1
[2.1.0]: https://github.com/ZBOSK-II/emtorch/compare/2.0.0...2.1.0
[2.0.0]: https://github.com/ZBOSK-II/emtorch/compare/1.3.0...2.0.0
[1.3.0]: https://github.com/ZBOSK-II/emtorch/compare/1.2.0...1.3.0
[1.2.0]: https://github.com/ZBOSK-II/emtorch/compare/1.1.0...1.2.0
[1.1.0]: https://github.com/ZBOSK-II/emtorch/compare/1.0.0...1.1.0
[1.0.0]: https://github.com/ZBOSK-II/emtorch/compare/0.1.0...1.0.0
[0.1.0]: https://github.com/ZBOSK-II/emtorch/releases/tag/0.1.0
