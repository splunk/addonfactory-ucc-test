import time
import pytest
from splunk_add_on_ucc_modinput_test.common import utils
from splunk_add_on_ucc_modinput_test.common import splunk_instance
from tests.modinput_functional import vendor_product
from tests.modinput_functional.ta import InputConfiguration

#   BE AWARE
#   the file content is extremely vendor product and TA specific
#   to be consistent with framework, you just need to keep test_internal_index
#   as the last function in the file

def test_foo_bar_group_creation(configuration):
    vendor_product.group_create(configuration.vendor_product_configuration)

    # get input that will be tested
    input_configuration = configuration.get_input_configuration("in_")
    time.sleep(input_configuration.interval)  #   input interval
    time.sleep(60)  #   just to give a little bit more time to get the data

    spl = f"search index={configuration.splunk_configuration.dedicated_index.name} action=group_created"
    utils.logger.debug(spl)
    search_result_details = splunk_instance.search(
        service=configuration.splunk_configuration.service, searchquery=spl
    )
    assert (
        search_result_details.result_count != 0
    ), f"Following query returned 0 events: {spl}"
    utils.logger.info(
        f"test_dedicated_index done at {utils.convert_to_utc(utils.get_epoch_timestamp())}"
    )


def test_foo_bar_group_deletion(configuration):
    vendor_product.group_delete(configuration.vendor_product_configuration)

    # get input that will be tested
    input_configuration = configuration.get_input_configuration("in_")
    time.sleep(input_configuration.interval)  #   input interval
    time.sleep(60)  #   just to give a little bit more time to get the data

    spl = f"search index={configuration.splunk_configuration.dedicated_index.name} action=group_deleted"
    utils.logger.debug(spl)
    search_result_details = splunk_instance.search(
        service=configuration.splunk_configuration.service, searchquery=spl
    )
    assert (
        search_result_details.result_count != 0
    ), f"Following query returned 0 events: {spl}"
    utils.logger.info(
        f"test_dedicated_index done at {utils.convert_to_utc(utils.get_epoch_timestamp())}"
    )


#   this test checks if none internal error occured
#   as such, has to be executed a the last one
def test_internal_index(configuration):
    spl = f"search index=_internal log_level IN (CRITICAL,ERROR,WARN) where _time>{utils.Common().start_timestamp}"
    utils.logger.debug(spl)
    search_result_details = splunk_instance.search(
        service=configuration.splunk_configuration.service, searchquery=spl
    )
    assert (
        search_result_details.result_count == 0
    ), f"Following query returned {search_result_details.result_count} events: {spl}"
    utils.logger.info(
        f"test_internal_index done at {utils.convert_to_utc(utils.get_epoch_timestamp())}"
    )
