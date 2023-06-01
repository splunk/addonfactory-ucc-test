# addonfactory-ucc-test
A framework to test UCC-based Splunk Add-ons.

splunk_add_on_ucc_modinput_test is aimed for TA modinput tests that currently involve vendor products becoming end to end tests.

1. If you want to apply this library for your TA, there three aspects you need to facus on and document:

    1.1. your TA 

        1.1.1. Configuration

What parameters need to be defined and in what order.
Are there common parameters?
Are there confidential parameters?
etc.

        1.1.2. Inputs

Do following for each modular input type

            1.1.2.1. What are values for common parameters for all modular inputs (you'll be able to define name prefix and interval; index will be set by the framework)?

            1.1.2.2. What are modular input type specific fields?

    1.2. vendor product

Focus on each unique event you are collecting with use of modular inputs
What actions need to be taken in vendor product to generate the event?
How the actions can be achieved programatically?

    1.3. Splunk

How does each unique event look like in Splunk?
What query needs to be applied to find particular event?
What are expected field values?
etc. 


2.  Once you are ready to add the tests to your TA project:

    2.1.    Open pyproject.toml and make sure following entries are there in tool.poetry.group.dev.dependencies stanza:
```
splunk-add-on-ucc-framework = "^5.27.0"
splunk-add-on-ucc-modinput-test = {git = "git@github.com:splunk/addonfactory-ucc-test.git"}
```

    2.2.    Run ucc-gen to generate output/[your TA name]/static/openapi.json

    2.3.    Run ucc-test-modinput init to have created for you:

        2.3.1.  swagger_client directory that contains:

            2.3.1.1.    client code for TA REST API

            2.3.1.2.    swagger_client/README.md file that documents the client API

This document will be used for tests/modinput_functional/ta.py customization

        2.3.2.  tests/modinput_functional/ directory that contain bleaprint for modinput tests

:exclamation: Due to limitations of dependant tools, ucc-test-modinput usage is limited to intel-based architectures.

3.  Customize tests/modinput_functional/*.py files

    3.1.    ta.py

        3.1.1.  setup

            3.1.1.1.    set loglevel to DEBUG

                3.1.1.1.1.  Find code snippet for splunk_ta_[vendor_product]_settings_logging_post in swagger_client/README.md

as an example:
```
try:
    api_response = api_instance.splunk_ta_jira_cloud_settings_logging_post(output_mode, loglevel=loglevel)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DefaultApi->splunk_ta_jira_cloud_settings_logging_post: %s\n" % e)
```

                3.1.1.1.2.  Paste the code snippet to the setup method and make sure arguments are assigned to expected value (in this case or variables in other cases)

All other details are organised for you (api_instance created, output_mode set to json, pprint and print aliased to logging debug and error respectively, etc.)
```
try:
    api_response = api_instance.splunk_ta_jira_cloud_settings_logging_post(output_mode, loglevel="DEBUG")
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DefaultApi->splunk_ta_jira_cloud_settings_logging_post: %s\n" % e)
```

            3.1.1.2.    create configuration

Use what you documented in point 1.1.1, to understand which *_post method from swagger_client/README.md needs to be used and in what order to set your TA Configuration programatically.
When customising relevant code snippets, use hints given in 3.1.1.1.2 as well as other good practices:

                3.1.1.2.1.  refer to self.vendor_product_configuration.[property] if some value is vendor specific configuration (eg. user name in the vendor product, access token or password, domain, etc.)
Make a list of such properties.

                3.1.1.2.2.  refer to self.[property] if that will be TA specific configuration - eg. some configuration name.
Remember to define properties like that in Configuration __init__ method. As an example - token_name that will be always prefixed by "tkn_" and suffix will contain timestamp for test timestamp (so will be unique for each test execution):
```
self.token_name = f"tkn_{utils.Common().sufix}"
```

            3.1.1.3.    create inputs

For each input type:

                3.1.1.3.1.  create relevant class that inherits from InputConfigurationBase that covers common parameters (see 1.1.2.1) and extends it (see 1.1.2.2)

                3.1.1.3.2.  in Configuration __init__ method create above class object(s) and add to inputs list (call add_input_configuration method)

                3.1.1.3.3.  in Configuration setup method iterate the input list `for input_configuration in self.get_all_inputs()`, test input_configuration object against classes defined in point 3.1.1.3.1 (`isinstance(x, [class inherited from InputConfigurationBase])`) and use code snippet(s) taken from swagger_client/README.md to call relevant api_instance *_post methods

        3.1.2.  teardown

Use algorithm given in point 3.1.1.3.2 to construct similar loop.
The difference will be that code snippets for *_name_post will be used with additional argument disabled, that should be set to True

    3.2.    vendor_product.py

        3.2.1.  Take point 1.2 and with use of vendor product documentation and other available resources, for each unique event, create a function that will be used to generate the event.
Make a list of vendor product configuration.

        3.2.2.  Define Configuration class with attributes

Take a list of attributes you prepared already in points 3.1.1.2.1 and 3.2.1
You can load the attribute values from environment variables
To do so, use utils.get_from_environment_variable. As an example, to load domain, username and token for product FooBar:
```
class Configuration:
    def __init__(self):
        self.domain = utils.get_from_environment_variable("MODINPUT_TEST_FOOBAR_DOMAIN")
        self.username = utils.get_from_environment_variable("MODINPUT_TEST_FOOBAR_USERNAME")
        self.token = utils.get_from_environment_variable("MODINPUT_TEST_FOOBAR_TOKEN")
```

    3.3.    test_modinputs.py

        3.3.1.  Construct test function for each unique event

            3.3.1.1.    The function has to accept `configuration` only

            3.3.1.2.    Call vendor_product.[function from pt. 3.2.1]

            3.3.1.3.    Get relevant input configuration and `time.sleep(input_configuration.interval + 60)`. 
The additional minute is to allow data to be propagated.
The value is just a proposition and in some cases different values may be appropriate

            3.3.1.4.    Create spl to get the unique event from dedicated splunk index

`spl = f"search index={configuration.splunk_configuration.dedicated_index.name} [other conditions like expected source, sourcetype, attribute value, etc.]"`

            3.3.1.5.    Run search (`splunk_instance.search`) and compare (assert) results with expected values

        3.3.2.  test_internal_index

Keep this test as the last one.
It checks internal log for warnings, errors and critical entries.
Time is limited to the modinput test execution

    3.4.    conftest.py

DO NOT MODIFY CODE IN THIS FILE

4.  When all necessary code modifications are ready, commit and push your modifications, except output and swagger_client directories

5.  If you want to run your modinput tests from just cloned repository:

    5.1.    Run ucc-gen and ucc-test-modinput to recreate output and swagger_client directories