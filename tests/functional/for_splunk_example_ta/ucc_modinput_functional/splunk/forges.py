from splunk_add_on_ucc_modinput_test.common import utils
from tests.ucc_modinput_functional import defaults
from tests.ucc_modinput_functional.splunk.client import SplunkClient
from tests.ucc_modinput_functional.vendor.client import VendorClient

from typing import Dict, Generator


def ta_logging(splunk_client: SplunkClient) -> Generator[None, None, None]:
    utils.logger.debug("Executing forge ta_logging")
    previous_log_level = splunk_client.get_ta_log_level()
    splunk_client.set_ta_log_level()
    yield
    splunk_client.set_ta_log_level(previous_log_level)


def _account_config(name: str, vendor_client: VendorClient) -> Dict[str, str]:
    return {
        "name": name,
        "api_key": vendor_client.config.api_key,
    }


def account(
    splunk_client: SplunkClient,
    vendor_client: VendorClient,
) -> Generator[Dict[str, str], None, None]:
    account_config = _account_config("ExampleAccount", vendor_client)
    splunk_client.create_account(**account_config)
    yield dict(
        account_config_name=account_config["name"]
    )  # yielded from forges dict key will be available as global variable
    # you can use in your tests to refer to yielded dict value


def another_account(
    splunk_client: SplunkClient,
    vendor_client: VendorClient,
) -> Generator[Dict[str, str], None, None]:
    account_config = _account_config("AnotherExampleAccount", vendor_client)
    splunk_client.create_account(**account_config)
    yield dict(another_account_config_name=account_config["name"])


def another_account_index(
    splunk_client: SplunkClient,
) -> Generator[Dict[str, str], None, None]:
    index_name = f"idx_mit_another_account_{utils.Common().sufix}"
    splk_conf = splunk_client.splunk_configuration
    splk_conf.create_index(
        index_name,
        splk_conf.service,
        is_cloud=splk_conf.is_cloud,
        acs_stack=splk_conf._acs_stack,
        acs_server=splk_conf.acs_server,
        splunk_token=splk_conf.token,
    )
    yield {"another_account_index_name": index_name}


def _account_input(
    splunk_client: SplunkClient,
    test_id: str,
    *,
    name: str,
    index: str,
    account: str,
    input_spl_name: str,
) -> Generator[Dict[str, str], None, None]:
    start_time = utils.get_epoch_timestamp()
    name += f"_{test_id}"
    account_input_config = dict(
        name=name,
        interval=defaults.INPUT_INTERVAL,
        index=index,
        account=account,
    )
    splunk_client.create_input(**account_input_config)
    input_spl = (
        f'search index={index} source="example://{name}" '
        f"| where _time>{start_time}"
    )
    # Take raw event into account when constructing the SPL; as an example:
    # extractions should be tested with pytest-splunk-addon
    yield {input_spl_name: input_spl}
    splunk_client.disable_input(name=name)


def account_input(
    splunk_client: SplunkClient,
    # vendor_client: VendorClient,
    test_id: str,
    account_config_name: str,
) -> Generator[Dict[str, str], None, None]:
    yield from _account_input(
        splunk_client=splunk_client,
        test_id=test_id,
        name="ExampleInput",
        index=splunk_client.splunk_configuration.dedicated_index.name,
        account=account_config_name,
        input_spl_name="example_input_spl",
    )
