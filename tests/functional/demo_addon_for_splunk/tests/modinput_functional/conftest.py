#   DO NOT MODIFY CODE IN THIS FILE
from typing import Generator
import pytest
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
        ta_configuration = create_ta_configuration_and_set_up()

    yield ta_configuration
    ta_configuration.tear_down(ta_configuration.api_instance)


#   DO NOT MODIFY CODE IN THIS FILE
