# Overview

addonfactory-ucc-test (AUT) is an open-source testing framework for functional tests for [UCC-based Splunk Add-ons](https://splunk.github.io/addonfactory-ucc-generator/) which allows to test add-ons functonality for data ingestion. It automates add-ons configuration, events generation by vendor product side and assessment of ingested events providing platform for end to end tests.

## Prerequisites

- Splunk instance with add-on installed
- the add-on [openapi.json](https://splunk.github.io/addonfactory-ucc-generator/openapi/#how-to-find-the-document)
- vendor product configured for the add-on


## Installation

addonfactory-ucc-test can be installed via pip from PyPI:

```console
pip3 install addonfactory-ucc-test
```

## Principles

The addonfactory-ucc-test framework follows principles in an order based on importance:

1. [add-on developer experience](./design_principles.md#developer-experience)

2. [execution time](./design_principles.md#performance)

3. [test scenarios complexity](./design_principles.md#complexity)

4. [data isolation](./design_principles.md#data-isolation)

5. [cross-platform & CI-ready](./design_principles.md#supported-platforms)


<!--
Refer to the [How to use](./how_to_use.md) section for detailed instructions on running the tests.

## Release notes

Find details about all the releases [here](https://github.com/splunk/addonfactory-ucc-test/releases).
-->