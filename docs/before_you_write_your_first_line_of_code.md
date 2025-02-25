# Before you write your first line of code

AUT is a powerful toolset.

Add-on developer experience is the most important for us and we don't want you to get lost in what is available for you.

### Learn from Splunk Add-on for Example

Before you start working on your own tests, check [splunk-example-ta](https://github.com/splunk/splunk-example-ta) to get some idea about the example TA. Think how you would test it.

Open `tests/ucc_modinput_functional` and go through it in proposed below order to see how it is tested. Are your ideas addressed?

#### tests/ucc_modinput_functional

1. `defaults.py` - contains predefined, the tests-specific, constant values

2. `vendor/` - contains vendor product-specific code

    1. `configuration.py` - to read configuration from environment variables; it can be used later for vendor product-specific means (eg. triggering action that would generate event available for add-on to collect), add-on configuration or within test functions

    2. `client.py` - contains code used to communicate with vendor product

3. `splunk/` - contains add-on specific code

    1. `client.py` - contains code used to communicate with add-on REST API; relevant code snippets can be found in swagger_client README.md copied from there, pasted to the client file and adopted

    2. `forges.py` - contains forge decorators; `yield` in each forge, separates setup and teardown

    3. `probes.py`

4. `test_configuration.py` - start simple, eg. from making sure the simplest case like `test_ta_logging` works fine. Keep adding following tests for add-on configuration to make sure you are able to define building blocks that will be used for inputs

5. `test_inputs.py` - you have proper configuration. There are still two things you need to confirm:

    1. Make sure vendor product is talkative enough to have always events available for your tests or you need to trigger events generation

    2. Input forge should return spl query you will use in input probe as well as in test to get raw events for assertion

### ... also worth considering

There are components you may still want to add to your tests:

1. `vendor/` 

    1. `forges.py` - use if you want to setup and teardown resources in vendor product

    2. `probes.py`

2. `splunk/`

    1. `configuration.py` - this file is to cover values not related to vendor product, such as proxy accounts

3. `test_proxies.py` - to test proxies. Proxy configuration is general for specific add-on, so if defined it will be used for all configuration entries as well as inputs. When constructing this kind of tests you want to isolate them that can be achieved by using `attach` decorator that would group following tasks:
    
    1. making sure proxy is defined as required (or disabled if we want to test without proxy configured)

    2. relevant configuration creation - especially if validation is used that requires relevant connection to vendor product

    3. input creation

    4. etc.

4. `test_validators.py` - to test improper values cannot be used when configuring add-on

5. etc.

Above is just a proposition that may be relevant for small to medium add-ons.

If you find you add-on more complex, feel free to organise the test structure the way you find the most convinient and efficient.

## ucc-test-modinput init

1. Make sure first:

    1. [the prerequsities are met](./index.md#prerequisites)

    2. [addonfactory-ucc-test is installed](index.md#installation)

2. Once you run `ucc-test-modinput init`[^1] , [`tests/ucc_modinput_functional`](#testsucc_modinput_functional) directory will be copied from the [example TA](https://github.com/splunk/splunk-example-ta) to your add-on repository.

3. Export Splunk parameters to [relevant environment variables](./addonfactory-ucc-test_pytest_plugin/#expected-environment-variables)

    2. You've got all the parameters that define your environment?

        1. Are there vendor product-specific, environment-specific, test-specific or other kind?

        2. Are there confidential parameters?

3. Follow [recommended order](#testsucc_modinput_functional) and hints given within the files when modifying them for your needs.

![Screen Recording](./images/output.gif)


[^1]: you may want to specify openapi.json file location (eg. if it is in `Downloads`: `ucc-test-modinput init --openapi-json ~/Downloads/openapi.json`); go to [`ucc-test-modinput` page](./ucc-test-modinput_cli_tool.md) for more