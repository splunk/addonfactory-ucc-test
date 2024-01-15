import time
from splunk_add_on_ucc_modinput_test.common import utils, splunk_instance
from splunk_add_on_ucc_modinput_test.common.tests import (
    before_and_after_test_checker,
)
from tests.modinput_functional import vendor_product
import logging

#   BE AWARE
#   the file content is extremely vendor product and TA specific
#   to be consistent with framework, you just need to keep test_internal_index
#   as the last function in the file
utils.logger.setLevel(logging.DEBUG)


def patch_endpoint1_check(configuration):
    message = "endpoint_1 patched for tests"
    vendor_product.patch_endpoint1(
        configuration.vendor_product_configuration,
        message=message,
    )

    input_configuration = configuration.get_input_configuration("in1_")
    time.sleep(input_configuration.interval)

    spl = f'search index=\
        {configuration.splunk_configuration.dedicated_index.name} "{message}" \
            | where _time>{utils.Common().start_timestamp}'
    utils.logger.debug(spl)
    search_result_details = splunk_instance.search(
        service=configuration.splunk_configuration.service, searchquery=spl
    )
    assert (
        search_result_details.result_count != 0
    ), f"Following query returned 0 events: {spl}"
    utils.logger.info(
        f"test_dedicated_index done at \
            {utils.convert_to_utc(utils.get_epoch_timestamp())}"
    )


def patch_endpoint2_check(configuration):
    message = "endpoint_2 patched for tests"
    vendor_product.patch_endpoint2(
        configuration.vendor_product_configuration, message=message
    )

    # get input that will be tested
    input_configuration = configuration.get_input_configuration("in2_")
    time.sleep(input_configuration.interval)

    spl = f'search index=\
        {configuration.splunk_configuration.dedicated_index.name} "{message}" \
            | where _time>{utils.Common().start_timestamp}'
    utils.logger.debug(spl)
    search_result_details = splunk_instance.search(
        service=configuration.splunk_configuration.service, searchquery=spl
    )
    assert (
        search_result_details.result_count != 0
    ), f"Following query returned 0 events: {spl}"
    utils.logger.info(
        f"test_dedicated_index done at \
            {utils.convert_to_utc(utils.get_epoch_timestamp())}"
    )


def patch_endpoint3_check(configuration):
    message = "endpoint_3 patched for tests"
    vendor_product.patch_endpoint3(
        configuration.vendor_product_configuration, message=message
    )

    input_configuration = configuration.get_input_configuration("in3_")
    time.sleep(input_configuration.interval)

    spl = f'search index=\
        {configuration.splunk_configuration.dedicated_index.name} "{message}" \
            | where _time>{utils.Common().start_timestamp}'
    utils.logger.debug(spl)
    search_result_details = splunk_instance.search(
        service=configuration.splunk_configuration.service, searchquery=spl
    )
    assert (
        search_result_details.result_count != 0
    ), f"Following query returned 0 events: {spl}"
    utils.logger.info(
        f"test_dedicated_index done at \
            {utils.convert_to_utc(utils.get_epoch_timestamp())}"
    )


@before_and_after_test_checker
def test_patch_endpoint1_0(configuration):
    patch_endpoint1_check(configuration=configuration)


@before_and_after_test_checker
def test_patch_endpoint2_0(configuration):
    patch_endpoint2_check(configuration=configuration)


@before_and_after_test_checker
def test_patch_endpoint3_0(configuration):
    patch_endpoint3_check(configuration=configuration)


@before_and_after_test_checker
def test_patch_endpoint1_1(configuration):
    patch_endpoint1_check(configuration=configuration)


@before_and_after_test_checker
def test_patch_endpoint2_1(configuration):
    patch_endpoint2_check(configuration=configuration)


@before_and_after_test_checker
def test_patch_endpoint3_1(configuration):
    patch_endpoint3_check(configuration=configuration)


@before_and_after_test_checker
def test_patch_endpoint1_2(configuration):
    patch_endpoint1_check(configuration=configuration)


@before_and_after_test_checker
def test_patch_endpoint2_2(configuration):
    patch_endpoint2_check(configuration=configuration)


@before_and_after_test_checker
def test_patch_endpoint3_2(configuration):
    patch_endpoint3_check(configuration=configuration)


@before_and_after_test_checker
def test_patch_endpoint1_3(configuration):
    patch_endpoint1_check(configuration=configuration)


@before_and_after_test_checker
def test_patch_endpoint2_3(configuration):
    patch_endpoint2_check(configuration=configuration)


@before_and_after_test_checker
def test_patch_endpoint3_3(configuration):
    patch_endpoint3_check(configuration=configuration)


@before_and_after_test_checker
def test_patch_endpoint1_4(configuration):
    patch_endpoint1_check(configuration=configuration)


@before_and_after_test_checker
def test_patch_endpoint2_4(configuration):
    patch_endpoint2_check(configuration=configuration)


@before_and_after_test_checker
def test_patch_endpoint3_4(configuration):
    patch_endpoint3_check(configuration=configuration)


@before_and_after_test_checker
def test_patch_endpoint1_5(configuration):
    patch_endpoint1_check(configuration=configuration)


@before_and_after_test_checker
def test_patch_endpoint2_5(configuration):
    patch_endpoint2_check(configuration=configuration)


@before_and_after_test_checker
def test_patch_endpoint3_5(configuration):
    patch_endpoint3_check(configuration=configuration)


@before_and_after_test_checker
def test_patch_endpoint1_6(configuration):
    patch_endpoint1_check(configuration=configuration)


@before_and_after_test_checker
def test_patch_endpoint2_6(configuration):
    patch_endpoint2_check(configuration=configuration)


@before_and_after_test_checker
def test_patch_endpoint3_6(configuration):
    patch_endpoint3_check(configuration=configuration)


@before_and_after_test_checker
def test_patch_endpoint1_7(configuration):
    patch_endpoint1_check(configuration=configuration)


@before_and_after_test_checker
def test_patch_endpoint2_7(configuration):
    patch_endpoint2_check(configuration=configuration)


@before_and_after_test_checker
def test_patch_endpoint3_7(configuration):
    patch_endpoint3_check(configuration=configuration)


@before_and_after_test_checker
def test_patch_endpoint1_8(configuration):
    patch_endpoint1_check(configuration=configuration)


@before_and_after_test_checker
def test_patch_endpoint2_8(configuration):
    patch_endpoint2_check(configuration=configuration)


@before_and_after_test_checker
def test_patch_endpoint3_8(configuration):
    patch_endpoint3_check(configuration=configuration)


@before_and_after_test_checker
def test_patch_endpoint1_9(configuration):
    patch_endpoint1_check(configuration=configuration)


@before_and_after_test_checker
def test_patch_endpoint2_9(configuration):
    patch_endpoint2_check(configuration=configuration)


@before_and_after_test_checker
def test_patch_endpoint3_9(configuration):
    patch_endpoint3_check(configuration=configuration)
