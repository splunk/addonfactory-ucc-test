# When you write your tests

Running [`ucc-test-modinput init`](./before_you_write_your_first_line_of_code.md#ucc-test-modinput-init) provides a starting point for further development.

Start with the [basic case](./test_scenarios.md#basic-scenario) even if you need to cover more complex test cases. This will allow you to ensure there is access from the development environment to the vendor product.

This paragraph contains hints that should be useful for your test development.

Keep checking [the example](./before_you_write_your_first_line_of_code.md#learn-from-splunk-add-on-for-example) for implementation details.

## Vendor product

### General hints

Vendor product specific code is entirely in developer's hands. There are however some hints you may find useful:

1. **Consult Product Documentation**:  
   Begin with the official product documentation. These resources often include code samples and integration guides that can be directly applied to your tests, saving development time and effort.

2. **Explore Official Repositories**:  
   Check vendor official repositories (eg. GitHub). These repositories might contain supporting libraries or example code that can aid in developing integrations.

3. **Leverage Package Indexes**:  
   Utilize PyPI.org or equivalent package indexes for discovering SDKs and libraries that are specific to the vendor products. These SDKs can simplify the integration process and ensure compatibility.

4. **Utilize OpenAPI Specifications**:  
   If available, use OpenAPI or equivalent specifications to create or generate client libraries for the vendor products. This can facilitate a more streamlined and automated integration process.

5. **Engage with Developer Communities**:  
   Platforms like Reddit and StackOverflow are valuable for community support. You can find discussions, troubleshooting tips, and shared experiences related to integrating vendor products.

6. **Consult AI Tools**:  
   Consider using AI services to assist with coding, integration challenges, or generating documentation. These tools can provide insights or generate code snippets that may enhance your framework.

### Framework specific hints

It is highly recommended to stay consistent with Splunk specific code to have internally consistent and easier to maintain tests. To achieve it, consider following hints:

1. Follow `vendor/` directory structure as described in [the example TA](./before_you_write_your_first_line_of_code.md#learn-from-splunk-add-on-for-example)

2. Store credentials in environment variables and use `get_from_environment_variable` from `splunk_add_on_ucc_modinput_test.common.utils` to read the credentials

    1. if environment variable is optional, use `is_optional=True` parameter - eg.:

    ```
    self.username = utils.get_from_environment_variable("MODINPUT_TEST_FOOBAR_USERNAME", is_optional=True)
    ```
    `None` will be assigned to `self.username` in example as above

    2. if environent variable should be encoded, use relevant sufix to emphasize a fact it was done and use `string_function` parameter when calling `get_from_environment_variable` function - eg.:
    ```
    self.token = utils.get_from_environment_variable("MODINPUT_TEST_FOOBAR_TOKEN_BASE64", string_function=utils.Base64.decode)
    ```
    in example as above:
        
        - `_BASE64` suffix is used to emphasize the password value should be base64 encoded
        
        - `string_function` is pointing to callable object that will do string transformation.

## Splunk

Proper spl query construction is crucial for proper tests results and performance.

The spl query format looks like below:

```
search index={index_name} source={source_name_containing_input_name} {raw_event_specific_string} | where _time>{start_time}
```
where:

- **index_name** can be:

      - default - assigned to `splunk_client.splunk_configuration.dedicated_index.name`

      - dedicated - check [data isolation principle](./design_principles.md#data-isolation) or [relevant test scenario](./test_scenarios.md#isolate-data-in-indexes) for more

- **source_name_containing_input_name** highly depends on add-on implementation; eg. for example add-on source part of the spl is defined as `source="example://{name}"` (where `name` is for input name)

- **raw_event_specific_string** that can be skipped, if other values are sufficient, one or many strings that define uniquely raw event we are interested in

- **start_time** - epoch timestamp should be used, however where timestamp is collected should be pick with special care. Check [test scenarios](./test_scenarios.md) to understand what potential options you've got. Timestamp of begginig of tests can be used as default: `start_time = utils.get_epoch_timestamp()`

# When your tests are ready

1. Export environment variables for [Splunk](./addonfactory-ucc-test_pytest_plugin.md#expected-environment-variables) and for [vendor](#framework-specific-hints)

2. Run tests: `pytest tests/ucc_modinput_functional/` (and fix tests if needed)

3. Commit and push your modifications to code repository. Ignore `output/` and `swagger_client/` directories that are generated by `ucc-gen` and `ucc-test-modinput` respectively.