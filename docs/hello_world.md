# Hello World example

This, step by step, instruction uses Splunk_TA_Example to show how you can create end to end, functional, modinput tests for your add-on.

If you want to make a lab exercise, clone [the repository](https://github.com/splunk/splunk-example-ta) to your workstation and create dedicated directory for the tests (eg. splunk-example-ta-test), so it can look like:
```
.
├── splunk-example-ta
└── splunk-example-ta-test
```

## [Satisfy prerequisites](./index.md#prerequisites)

Open `splunk-example-ta/` in terminal.

???- note "Click to check where we are with the prerequisites"

    - [ ] Prepared basic setup for the add-on

        - [ ] Vendor product configured for the add-on

        - [ ] Splunk instance with add-on installed

        - [ ] The setup is manually tested

    - [ ] [openapi.json](https://splunk.github.io/addonfactory-ucc-generator/openapi/#how-to-find-the-document) saved to developer workstation

    - [ ] docker installed and started

Example TA for Splunk comes with script that automates environment setup.

The script requires docker, so **make sure that docker installed and started**.

???- note "Click to check where we are with the prerequisites"

    - [ ] Prepared basic setup for the add-on

        - [ ] Vendor product configured for the add-on

        - [ ] Splunk instance with add-on installed

        - [ ] The setup is manually tested

    - [ ] [openapi.json](https://splunk.github.io/addonfactory-ucc-generator/openapi/#how-to-find-the-document) saved to developer workstation

    - [x] **docker installed and started**

Run following script 
```console
./scripts/run_locally.sh
```
to get:

- server-example-ta that exposes `events` endpoint on port 5000

- splunk-example-ta that is Splunk instance exposing standard ports (we'll be interested in 8000 - web and 8089 - management port) with example TA installed.
???- note "Click to check where we are with the prerequisites"

    - [ ] Prepared basic setup for the add-on

        - [x] **Vendor product configured for the add-on**

        - [x] **Splunk instance with add-on installed**

        - [ ] The setup is manually tested

    - [ ] [openapi.json](https://splunk.github.io/addonfactory-ucc-generator/openapi/#how-to-find-the-document) saved to developer workstation

    - [x] docker installed and started

There is another script that creates Example TA configuration and inputs:

```console
./scripts/local_testing_setup.sh
```

You can verify both scripts results by:

- opening the splunk instance: http://localhost:8000

- signing in (admin / [Chang3d!](https://github.com/splunk/splunk-example-ta/blob/26225f0c1ca6aeb3897696918898d0980eac82e9/docker-compose.yml#L16))

- checking [configuration](http://localhost:8000/en-GB/app/Splunk_TA_Example/configuration) and [inputs](http://localhost:8000/en-GB/app/Splunk_TA_Example/inputs)

- [searching events](http://localhost:8000/en-GB/app/search/search?q=search%20index%20%3D%20*)

???- note "Click to check where we are with the prerequisites"

    - [x] **Prepared basic setup for the add-on**

        - [x] Vendor product configured for the add-on

        - [x] Splunk instance with add-on installed

        - [x] **The setup is manually tested**

    - [ ] [openapi.json](https://splunk.github.io/addonfactory-ucc-generator/openapi/#how-to-find-the-document) saved to developer workstation

    - [x] docker installed and started

Open [configuration](http://localhost:8000/en-GB/app/Splunk_TA_Example/configuration) and download it to `splunk-example-ta-test/` directory using [OpenAPI.json button](https://splunk.github.io/addonfactory-ucc-generator/openapi/#how-to-find-the-document).

???- note "Click to check where we are with the prerequisites"

    - [x] Prepared basic setup for the add-on

        - [x] Vendor product configured for the add-on

        - [x] Splunk instance with add-on installed

        - [x] The setup is manually tested

    - [x] **[openapi.json](https://splunk.github.io/addonfactory-ucc-generator/openapi/#how-to-find-the-document) saved to developer workstation**

    - [x] docker installed and started


You've got openapi.json that will be used in following steps. Moreover, you confirmed that you've got all you need to create necessary environment for development. You can delete docker containers
```console
docker rm -f server-example-ta splunk-example-ta
```
and recreate the environment
```console
./scripts/run_locally.sh
```

**Note:** The containers recreation is just one of a few options to prepare the environment for development. If you are not interested in having clean instance, you may consider:

- inputs deactivation only

- inputs and configuration deletion

- etc.

## init

Open `splunk-example-ta-test/` directory in terminal. There should be openapi.json file downloaded as a part of [satisfying prerequisities](#satisfy-prerequisites).

[Install `addonfactory-ucc-test` and make sure it is installed](./index.md#installation)
```console
pip install addonfactory-ucc-test
ucc-test-modinput --version
```

[Initialize modinput tests](./before_you_write_your_first_line_of_code.md#ucc-test-modinput-init)
```console
ucc-test-modinput init --openapi-json openapi.json
```
Your subdirecotries structure should look like
```
.
├── swagger_client
│   ├── api
│   └── models
└── tests
    └── ucc_modinput_functional
        ├── splunk
        │   └── client
        └── vendor
            └── client
```

**Hint:** If you use version control system such as git, you don't want to keep there `swagger_client/` that will be generated for you from `openapi.json` by `ucc-test-modinput`.

[Set environment variables for your Splunk instance.](./addonfactory-ucc-test_pytest_plugin.md#expected-environment-variables)
```console
export MODINPUT_TEST_SPLUNK_HOST=localhost
export MODINPUT_TEST_SPLUNK_PORT=8089
export MODINPUT_TEST_SPLUNK_USERNAME=admin
export MODINPUT_TEST_SPLUNK_PASSWORD_BASE64=$(ucc-test-modinput base64encode -s 'Chang3d!')
```

Run few auto-generated tests 
```console
pytest tests/ucc_modinput_functional
```
You should be informed about 3 passed tests.

We will be interested in `splunk-example-ta-test/tests/ucc_modinput_functional/` when working on following points of the instruction
```
.
├── README.md
├── __init__.py
├── defaults.py
├── splunk
│   ├── __init__.py
│   ├── client
│   │   ├── __init__.py
│   │   ├── _managed_client.py
│   │   ├── client.py
│   │   └── configuration.py
│   ├── forges.py
│   └── probes.py
├── test_settings.py
└── vendor
    ├── __init__.py
    ├── client
    │   ├── __init__.py
    │   ├── client.py
    │   └── configuration.py
    ├── forges.py
    └── probes.py
```

## test_ta_logging - your first test

We want to have log level set to DEBUG for all of the tests we will write.

As the log level will be so common, we can add it to `defaults.py`
```
TA_LOG_LEVEL_FOR_TESTS = "DEBUG"
```

We will create appropriate test, to make sure log level is changed to DEBUG.

Let's have dedicated file to test modifications in addon configuration - `test_configuration.py`. Move piece of code for log level from `test_settings.py` to `test_configuration.py` and adopt.

The code we are to use from `test_settings.py`
```
@attach(forge(set_loglevel, loglevel="CRITICAL", probe=wait_for_loglevel))
def test_valid_loglevel(splunk_client: SplunkClient, wait_for_loglevel: bool) -> None:
    assert wait_for_loglevel is True
```

The code how it should look like in `test_configuration.py`
```
@bootstrap(
    forge(
        set_loglevel,
        loglevel=defaults.TA_LOG_LEVEL_FOR_TESTS,
        probe=wait_for_loglevel,
    )
)
def test_ta_logging(splunk_client: SplunkClient) -> None:
    assert (
        splunk_client.get_settings_logging()["loglevel"]
        == defaults.TA_LOG_LEVEL_FOR_TESTS
    )
```
You need add few imports to make it works
```
from splunk_add_on_ucc_modinput_test.functional.decorators import (
    bootstrap,
    forge,
)
from tests.ucc_modinput_functional.splunk.forges import (
    set_loglevel,
)
from tests.ucc_modinput_functional.splunk.probes import (
    wait_for_loglevel,
)
from tests.ucc_modinput_functional.splunk.client import SplunkClient
from tests.ucc_modinput_functional import defaults
```
We are ready to run our first test. Remember to do it from `splunk-example-ta-test/`
```
pytest -v tests/ucc_modinput_functional/test_configuration.py
```
You should see
```
tests/ucc_modinput_functional/test_configuration.py::test_ta_logging PASSED [100%]
```
**Hint:** Save modifications to your version control system

## test_accounts - first, this addon-specific, test

We want to make sure account is created in addon configuration.

Account configuration requires server API key. That is configuration relevant to server-example-ta - vendor product.

API key is a credential. We would like to keep it as non-plain text environment variables. We need to document that for whoever will use our test.

Open `splunk-example-ta-test\tests/ucc_modinput_functional/README.md` and add relevant information there.
```
Alongside with environment variables for Splunk, export API key for server-example-ta:

    ```console
    export MODINPUT_TEST_EXAMPLE_API_KEY_BASE64=$(ucc-test-modinput base64encode -s 'super-secret-api-token')
    ```
```
Once we can be sure the variable is defined, we want to read it. Open `splunk-example-ta-test/tests/ucc_modinput_functional/vendor/client/configuration.py`, make sure the key is read from the variable and expose for use:
```
class Configuration(VendorConfigurationBase):
    def customize_configuration(self) -> None:
        self._api_key = utils.get_from_environment_variable(
            "MODINPUT_TEST_EXAMPLE_API_KEY_BASE64",
            string_function=utils.Base64.decode,
        )

    @property
    def api_key(self) -> Optional[str]:
        return self._api_key
```
**Note:** Remember to `from typing import Optional`

Search `splunk-example-ta-test/tests/ucc_modinput_functional/splunk/client/_managed_client.py` for appropriate method for account creation - such as `create_account`.

You were already able to see (by `test_ta_logging` example) that test function is decorated with forge functions. Let's create one for the account in `splunk-example-ta-test/tests/ucc_modinput_functional/splunk/forges.py`
```
def account(
    splunk_client: SplunkClient,
    vendor_client: VendorClient,
) -> Generator[Dict[str, str], None, None]:
    account_config = {
        "name": "ExampleAccount",
        "api_key": vendor_client.config.api_key,
    }
    splunk_client.create_account(**account_config)
    yield dict(
        account_config_name=account_config["name"]
    )
```
**Note:** Remember to `from tests.ucc_modinput_functional.vendor.client import VendorClient`

We've got all of the blocks ready now to build our test function. Open `splunk-example-ta-test/tests/ucc_modinput_functional/test_configuration.py`
```
@bootstrap(
    forge(
        set_loglevel,
        loglevel=defaults.TA_LOG_LEVEL_FOR_TESTS,
        probe=wait_for_loglevel,
    ),
    forge(account),
)
def test_accounts(
    splunk_client: SplunkClient,
    account_config_name: str,
) -> None:
    actual_account = splunk_client.get_account(account_config_name)
    assert actual_account is not None
```
**Note:** Remember to `from tests.ucc_modinput_functional.splunk.forges import account`

We are ready to run test_accounts:
```
pytest -v tests/ucc_modinput_functional/test_configuration.py::test_accounts
```
You should get
```
tests/ucc_modinput_functional/test_configuration.py::test_accounts PASSED
```
**Hint:** Save modifications to your version control system


## test_inputs to make sure data is comming

We want to make sure input is created, data is ingested and input is deactivated. Goal is to have it available for troubleshooting if needed but we don't want to keep the Splunk instance too busy with inputs active once events necessary for tests were already ingested.

Let's find relevant methods to create and deactivate inputs in `splunk-example-ta-test/tests/ucc_modinput_functional/splunk/client/_managed_client.py` -- `create_example` and `update_example`.

When creating input, we'll use some default value for interval. Add following to `defaults.py`:
```
INPUT_INTERVAL = 60
```

In case of inputs, we want to be sure data is coming to specific index, source related to just created input and after the input gets created.

Whatever needs to happen before test execution, needs to be added before `yield` (test setup). `yield`ed are values used for tests, other forges, probes, etc. What happens after, needs to be added after `yield` (teardown).

Let's add `example_input` forge containing all the knowledge documented above to `tests/ucc_modinput_functional/splunk/forges.py`:
```
def example_input(
    splunk_client: SplunkClient,
    *,
    account_config_name: str,   # was defined in account forge
) -> Generator[Dict[str, str], None, None]:
    name = "ExampleInput"
    index = splunk_client.splunk_configuration.dedicated_index.name
    start_time = utils.get_epoch_timestamp()
    splunk_client.create_example(name, defaults.INPUT_INTERVAL, index, account_config_name)
    input_spl = (
        f'search index={index} source="example://{name}" '
        f"| where _time>{start_time}"
    )
    yield dict(input_spl_name=input_spl)
    splunk_client.update_example(name)
```
***Note:*** You need to add two imports:
```
from splunk_add_on_ucc_modinput_test.common import utils
from tests.ucc_modinput_functional import defaults
```

Once some configuration is added, modified or deleted and effect is not immediate, we use probes to wait with further steps until effects occur. Open `tests/ucc_modinput_functional/splunk/probes.py` and add `events_ingested`:
```
def events_ingested(
    splunk_client: SplunkClient, input_spl_name: str, probes_wait_time: int = 10
) -> Generator[int, None, None]:
    while True:
        search = splunk_client.search(searchquery=input_spl_name)
        if search.result_count != 0:
            break
        yield probes_wait_time
```

Input configuration requires account configuration that was tested in [previous section](#test_accounts-first-this-addon-specific-test). Moreover, just like for all the other tests, we want to make sure log level is set to default.

Let's have dedicated test file for inputs - `test_inputs.py` in `tests/ucc_modinput_functional/` with `test_input`:
```
@bootstrap(
    forge(
        set_loglevel,
        loglevel=defaults.TA_LOG_LEVEL_FOR_TESTS,
        probe=wait_for_loglevel,
    ),
    forge(account),
    forge(
        example_input,
        probe=events_ingested,
    )
)
def test_inputs(splunk_client: SplunkClient, input_spl_name: str) -> None:
    search_result_details = splunk_client.search(searchquery=input_spl_name)
    assert (
        search_result_details.result_count != 0
    ), f"Following query returned 0 events: {input_spl_name}"

    utils.logger.info(
        "test_inputs_loginhistory_clone done at "
        + utils.convert_to_utc(utils.get_epoch_timestamp())
    )
```
***Note:*** You need to have imports you have in `test_configuration.py` and few new:

- `from splunk_add_on_ucc_modinput_test.common import utils`

- `example_input` add to imports from `tests.ucc_modinput_functional.splunk.forges`

- `events_ingested` from `tests.ucc_modinput_functional.splunk.probes`

Run test_inputs:
```
pytest -v tests/ucc_modinput_functional/test_inputs.py::test_inputs
```
You should get
```
tests/ucc_modinput_functional/test_configuration.py::test_accounts PASSED
```
***Hint:*** Remember about saving to version control system

## ... want to see more examples?

Check [the tests implementation for Example TA](https://github.com/splunk/splunk-example-ta/tests/ucc_modinput_functional).
