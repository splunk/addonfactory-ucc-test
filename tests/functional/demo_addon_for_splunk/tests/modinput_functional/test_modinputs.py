import time
import pytest
from splunk_add_on_ucc_modinput_test.common import utils
from splunk_add_on_ucc_modinput_test.common import splunk_instance
from tests.modinput_functional import ta,vendor_product
import logging

#   BE AWARE
#   the file content is extremely vendor product and TA specific
#   to be consistent with framework, you just need to keep test_internal_index
#   as the last function in the file
utils.logger.setLevel(logging.DEBUG)

def test_patch_endpoint1(configuration):
    message = "endpoint_1 patched for tests"
    # vendor_product.patch_endpoint1(configuration.vendor_product_configuration, message=message)
    vendor_product.patch_endpoint(
        url='http://3.127.231.148:8080/endpoint1',    # configuration.vendor_product_configuration.endpoint1
        message=message)

    # get input that will be tested
    input_configuration = configuration.get_input_configuration("in1_") 
    time.sleep(30)  #   configuration.input_configuration.interval
    time.sleep(60)  #   just to give a little bit more time to get the data
    
    # construct spl the way it collects this test case events
    # use _raw data; eg. if your TA contains field extractions in props/transforms disable your TA when testing your spl
    spl = f"search index={configuration.splunk_configuration.dedicated_index.name} \"{message}\" | where _time>{utils.Common().start_timestamp}"
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


def test_patch_endpoint2(configuration):
    message = "endpoint_2 patched for tests"
    vendor_product.patch_endpoint1(configuration.vendor_product_configuration, message=message)

    # get input that will be tested
    input_configuration = configuration.get_input_configuration("in2_")
    time.sleep(input_configuration.interval)  #   input interval
    time.sleep(60)  #   just to give a little bit more time to get the data
    
    # construct spl the way it collects this test case events
    # use _raw data; eg. if your TA contains field extractions in props/transforms disable your TA when testing your spl
    spl = f"search index={configuration.splunk_configuration.dedicated_index.name} \"{message}\" | where _time>{utils.Common().start_timestamp}"
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


def test_patch_endpoint3(configuration):
    message = "endpoint_2 patched for tests"
    vendor_product.patch_endpoint1(configuration.vendor_product_configuration, message=message)

    # get input that will be tested
    input_configuration = configuration.get_input_configuration("in3_")
    time.sleep(input_configuration.interval)  #   input interval
    time.sleep(60)  #   just to give a little bit more time to get the data
    
    # construct spl the way it collects this test case events
    # use _raw data; eg. if your TA contains field extractions in props/transforms disable your TA when testing your spl
    spl = f"search index={configuration.splunk_configuration.dedicated_index.name} \"{message}\" | where _time>{utils.Common().start_timestamp}"
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
    spl = f"search index=_internal ({ta.NAME} OR source=*{ta.NAME}* OR sourcetype=*{ta.NAME}*) log_level IN (CRITICAL,ERROR) | where _time>{utils.Common().start_timestamp}"
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
