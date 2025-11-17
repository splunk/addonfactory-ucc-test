# Changelog

## [2.0.5](https://github.com/splunk/addonfactory-ucc-test/compare/v2.0.4...v2.0.5) (2025-11-17)


### Bug Fixes

* index creation in SHC ([#150](https://github.com/splunk/addonfactory-ucc-test/issues/150)) ([1991d1e](https://github.com/splunk/addonfactory-ucc-test/commit/1991d1e445e4d832b8bb1ae1a19a2d094a9af880))

## [2.0.4](https://github.com/splunk/addonfactory-ucc-test/compare/v2.0.3...v2.0.4) (2025-10-21)


### Bug Fixes

* splunk cloud identification ([#149](https://github.com/splunk/addonfactory-ucc-test/issues/149)) ([688b1d3](https://github.com/splunk/addonfactory-ucc-test/commit/688b1d391cfc51afeeebbcfd11ae0d16c4c03ecf))

## [2.0.3](https://github.com/splunk/addonfactory-ucc-test/compare/v2.0.2...v2.0.3) (2025-10-21)


### Bug Fixes

* splunk cloud identification ([#148](https://github.com/splunk/addonfactory-ucc-test/issues/148)) ([e22e777](https://github.com/splunk/addonfactory-ucc-test/commit/e22e77731217d381d2bef062e4c2fb70d720d12e))

## [2.0.2](https://github.com/splunk/addonfactory-ucc-test/compare/v2.0.1...v2.0.2) (2025-10-17)


### Bug Fixes

* increase backoff delay for index creation retries on 424/503 errors ([#147](https://github.com/splunk/addonfactory-ucc-test/issues/147)) ([6e03f0d](https://github.com/splunk/addonfactory-ucc-test/commit/6e03f0d09d656d23e93b6b793515913a1a19c486))

## [2.0.1](https://github.com/splunk/addonfactory-ucc-test/compare/v2.0.0...v2.0.1) (2025-08-25)


### Bug Fixes

* update index creation for azure cloud instance ([#144](https://github.com/splunk/addonfactory-ucc-test/issues/144)) ([d67d22d](https://github.com/splunk/addonfactory-ucc-test/commit/d67d22dde9628e984d2551e62e45c691fb736d22))

# [2.0.0](https://github.com/splunk/addonfactory-ucc-test/compare/v1.0.1...v2.0.0) (2025-08-08)


### Features

* add support for creating metric index ([c9f9e00](https://github.com/splunk/addonfactory-ucc-test/commit/c9f9e003e2b42d4dc1b5f973432f4b9ba926fca9))
* add support for creating metric index ([#134](https://github.com/splunk/addonfactory-ucc-test/issues/134)) ([38cfd58](https://github.com/splunk/addonfactory-ucc-test/commit/38cfd582910b7c74bbc4388510dd0870b78d4f99))
* release 2.0.0 ([#135](https://github.com/splunk/addonfactory-ucc-test/issues/135)) ([8516563](https://github.com/splunk/addonfactory-ucc-test/commit/85165635e83198e275b8b58022ceb16b7fe62dd2))
* search for all types of indexes in get_index ([35ef4b5](https://github.com/splunk/addonfactory-ucc-test/commit/35ef4b55ddd12bf77399cfdc6e3a54afc745adc6))
* support kvstore api ([#131](https://github.com/splunk/addonfactory-ucc-test/issues/131)) ([930a076](https://github.com/splunk/addonfactory-ucc-test/commit/930a0760a3debc57ce75e1ab4dac810171e60961))


### BREAKING CHANGES

* change get_index method interface so it's able to get
indexes from idm stacks.

### PR Type

**What kind of change does this PR introduce?**
* [X] Feature
* [ ] Bug Fix
* [ ] Refactoring (no functional or API changes)
* [X] Documentation Update
* [ ] Maintenance (dependency updates, CI, etc.)

## Summary

Test runs:

https://cd.splunkdev.com/taautomation/ta-automation-compatibility-tests/-/pipelines/28335229

https://cd.splunkdev.com/taautomation/ta-automation-compatibility-tests/-/pipelines/28340518

https://cd.splunkdev.com/taautomation/ta-automation-compatibility-tests/-/pipelines/28533993

https://cd.splunkdev.com/taautomation/ta-automation-compatibility-tests/-/pipelines/28533938
### Changes

Please provide a summary of the changes.

### User experience

Please describe the user experience before and after this change.
Screenshots are welcome for additional context.

## Checklist

If an item doesn't apply to your changes, leave it unchecked.

* [X] I have performed a self-review of this change according to the
[development
guidelines](https://splunk.github.io/addonfactory-ucc-test/contributing/#development-guidelines)
* [X] Tests have been added/modified to cover the changes [(testing
doc)](https://splunk.github.io/addonfactory-ucc-test/contributing/#build-and-test)
* [X] Changes are documented
* [X] PR title and description follows the [contributing
principles](https://splunk.github.io/addonfactory-ucc-test/contributing/#pull-requests)

## [1.0.1](https://github.com/splunk/addonfactory-ucc-test/compare/v1.0.0...v1.0.1) (2025-07-02)


### Bug Fixes

* add error handling while tests collection ([#108](https://github.com/splunk/addonfactory-ucc-test/issues/108)) ([263b900](https://github.com/splunk/addonfactory-ucc-test/commit/263b900e885901acb99ea9a3d2e99fa4047c257e))
* set proper attribute name for token ([#120](https://github.com/splunk/addonfactory-ucc-test/issues/120)) ([ea0eb1d](https://github.com/splunk/addonfactory-ucc-test/commit/ea0eb1d81045120f37ab1af87a2a2c2205ec36c4))

# 1.0.0 (2025-05-27)
