#   DO NOT MODIFY CODE IN THIS FILE
from typing import Generator
from filelock import FileLock
import json
import pytest
from splunk_add_on_ucc_modinput_test.common import utils
from splunk_add_on_ucc_modinput_test.common.splunk_instance import (
    Configuration as SplunkConfiguration,
)
from tests.modinput_functional.vendor_product import (
    Configuration as VendorProductConfiguration,
)
from tests.modinput_functional.ta import Configuration as TaConfiguration


#   DO NOT MODIFY CODE IN THIS FILE
def create_ta_configuration_and_set_up() -> TaConfiguration:
    ta_configuration = TaConfiguration(
        splunk_configuration=SplunkConfiguration(),
        vendor_product_configuration=VendorProductConfiguration(),
    )
    ta_configuration.set_up(ta_configuration.api_instance)
    return ta_configuration


@pytest.fixture(scope="session")
def configuration(
    tmp_path_factory: pytest.TempPathFactory, worker_id: str
) -> Generator[TaConfiguration, None, None]:
    # ta_configuration = TaConfiguration(
    #     splunk_configuration=SplunkConfiguration(),
    #     vendor_product_configuration=VendorProductConfiguration(),
    # )
    # ta_configuration.set_up(ta_configuration.api_instance)
    if not worker_id:
        ta_configuration = TaConfiguration(
            splunk_configuration=SplunkConfiguration(),
            vendor_product_configuration=VendorProductConfiguration(),
        )
        ta_configuration.set_up(ta_configuration.api_instance)
    else:
        # get the temp directory shared by all workers
        root_tmp_dir = tmp_path_factory.getbasetemp().parent

        fn = root_tmp_dir / "data.json"
        with FileLock(str(fn) + ".lock"):
            if fn.is_file():
                data = json.loads(fn.read_text())
                utils.Common().start_timestamp = float(data)
                ta_configuration = TaConfiguration(
                    splunk_configuration=SplunkConfiguration(),
                    vendor_product_configuration=VendorProductConfiguration(),
                )
            # ta_configuration.set_up(ta_configuration.api_instance)
            else:
                data = utils.Common().start_timestamp
                fn.write_text(json.dumps(data))
                ta_configuration = TaConfiguration(
                    splunk_configuration=SplunkConfiguration(),
                    vendor_product_configuration=VendorProductConfiguration(),
                )
                ta_configuration.set_up(ta_configuration.api_instance)
        # return data

    yield ta_configuration
    # ta_configuration.tear_down(ta_configuration.api_instance)
    pass


#   DO NOT MODIFY CODE IN THIS FILE
