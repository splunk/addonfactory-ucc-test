# Overview

addonfactory-ucc-test (AUT) is an open-source testing framework for functional tests for [UCC-based Splunk Add-ons](https://splunk.github.io/addonfactory-ucc-generator/) which allows to test add-ons functonality for data ingestion. It automates add-ons configuration, events generation by vendor product side and assessment of ingested events providing platform for end to end tests.

## Principles

The addonfactory-ucc-test framework follows principles in an order based on importance:

1. [add-on developer experience](./before_you_write_your_first_line_of_code.md)

2. [execution time](./design_principles.md#performance)

3. [test scenarios complexity](./design_principles.md#complexity)

4. [data isolation](./design_principles.md#data-isolation)

5. [cross-platform & CI-ready](./design_principles.md#supported-platforms)

## Building blocks

The addonfactory-ucc-test framework consists of following building blocks:

- addonfactory-ucc-test that contains:

    - [`ucc-test-modinput` CLI tool](./ucc-test-modinput_cli_tool.md) used to initialise the tests (creates relevant directories, files and initial test; one time action), generate add-on SDK and other supporting actions (text encryption and decryption) 

    - [`addonfactory-ucc-test/functional` pytest plugin](./addonfactory-ucc-test_pytest_plugin.md) used to extend pytest functionality to support end-to-end functional tests 

- supporting artifacts:

    - `ucc_modinput_functional` tests in [`Splunk Add-on for Example` ](https://github.com/splunk/splunk-example-ta)

    - this documentation


## Installation

addonfactory-ucc-test can be installed via pip from PyPI:

```console
pip3 install addonfactory-ucc-test
```

## Prerequisites

- Prepared basic setup for the add-on
    - Vendor product configured for the add-on
    - Splunk instance with add-on installed
    - The setup is manually tested
- [openapi.json](https://splunk.github.io/addonfactory-ucc-generator/openapi/#how-to-find-the-document) saved to developer workstation

