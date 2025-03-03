

    3.3.    test_modinputs.py

        3.3.1.  Construct test function for each unique event

            3.3.1.1.    The function has to accept `configuration` only

            3.3.1.2.    Call vendor_product.[function from pt. 3.2.1]

            3.3.1.3.    Get relevant input configuration and `time.sleep(input_configuration.interval + 60)`. 
The additional minute is to allow data to be propagated.
The value is just a proposition and in some cases different values may be appropriate

            3.3.1.4.    Make sure you are setting `test_start_timestamp` and `test_end_timestamp` (`test_end_timestamp = utils.get_epoch_timestamp()`)

            3.3.1.5.    Create spl to get the unique event from dedicated splunk index

`spl = f"search index={input_configuration.index} [other conditions like expected source, sourcetype, attribute value, etc.] | where _time>{test_start_timestamp} AND _time<{test_end_timestamp}"`

            3.3.1.6.    Run search (`splunk_instance.search`) and compare (assert) results with expected values

        3.3.2.  test_internal_index

Keep this test as the last one.
It checks internal log for warnings, errors and critical entries.
Time is limited to the modinput test execution

    3.4.    conftest.py

DO NOT MODIFY CODE IN THIS FILE

4. Set environment variables and pytest run:

    4.1.    Splunk

        4.1.1.  common for all Splunk architectures and usecases
```
export MODINPUT_TEST_SPLUNK_HOST=[your_value; eg. localhost]
export MODINPUT_TEST_SPLUNK_PORT=[your_value; eg. 8089]
export MODINPUT_TEST_SPLUNK_USERNAME=[your_value; eg. admin]
export MODINPUT_TEST_SPLUNK_PASSWORD_BASE64=[your_value]
```
If you use Splunk Enterprise and want to have dedicated index created for each test run, that's all you need to define for Splunk.

        4.1.2.  if you want to use existing index (for both architectures)
`export MODINPUT_TEST_SPLUNK_DEDICATED_INDEX=[existing_index_name]`

        4.1.3. if you use Splunk Cloud and want to have dedicated index created for each test run
```
export MODINPUT_TEST_SPLUNK_TOKEN_BASE64=[base64_encoded_Splunk_token]
export MODINPUT_TEST_ACS_SERVER=[ACS_server eg. https://staging.admin.splunk.com]
export MODINPUT_TEST_ACS_STACK=[ACS_stack eg. if your instance address is https://my-splunk.splunkcloud.com/, most likely, your stack is my-splunk]
```


    4.2.    TA

Check 3.2.2 for your list. What's given below is just an example 
```
export MODINPUT_TEST_FOOBAR_DOMAIN=[your_value]
export MODINPUT_TEST_FOOBAR_USERNAME=[your_value]
export MODINPUT_TEST_FOOBAR_TOKEN_BASE64=[your_value]
```

    4.3. `poetry run pytest tests/modinput_functional/`

5.  When all necessary code modifications are ready, commit and push your modifications (except output and swagger_client directories that are generated during ucc-gen and ucc-test-modinput respectively)

6.  If you want to run your modinput tests from just cloned repository:

    6.1.    Run ucc-gen and ucc-test-modinput to recreate output and swagger_client directories

    6.2.    Set environment variables and pytest run; check pt. 4. for details
