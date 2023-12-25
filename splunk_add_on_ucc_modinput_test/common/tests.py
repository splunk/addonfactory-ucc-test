import functools
from splunk_add_on_ucc_modinput_test.common import utils
from splunk_add_on_ucc_modinput_test.common import splunk_instance
from tests.modinput_functional.ta import Configuration as TaConfiguration
import logging
from collections.abc import Callable

utils.logger.setLevel(logging.DEBUG)


def internal_index_check(*, configuration: TaConfiguration) -> None:
    spl = f"search index=_internal ({configuration.NAME} OR \
        source=*{configuration.NAME}* OR sourcetype=*{configuration.NAME}*) \
        log_level IN (CRITICAL,ERROR) \
        | where _time>{utils.Common().start_timestamp}"
    utils.logger.debug(spl)
    search_result_details = splunk_instance.search(
        service=configuration.splunk_configuration.service, searchquery=spl
    )
    assert (
        search_result_details.result_count == 0
    ), f"Following query returned {search_result_details.result_count} events: \
        {spl}"
    utils.logger.info(
        f"test_internal_index done at \
            {utils.convert_to_utc(utils.get_epoch_timestamp())}"
    )


def before_test_checker(
    *, configuration: TaConfiguration, test_function_name: str
) -> None:
    # utils.logger.debug(
    #     f'before_test_checker run for test function {test_function_name}'
    # )
    pass


def after_test_checker(
    *, configuration: TaConfiguration, test_function_name: str
) -> None:
    utils.logger.debug(
        f"after_test_checker run for test function {test_function_name}"
    )
    internal_index_check(configuration=configuration)


def before_and_after_test_checker(
    test_function: Callable[[TaConfiguration], None]
):
    @functools.wraps(test_function)
    def wrapper(*, configuration: TaConfiguration) -> None:
        before_test_checker(
            configuration=configuration,
            test_function_name=test_function.__name__,
        )
        result = test_function(configuration)
        after_test_checker(
            configuration=configuration,
            test_function_name=test_function.__name__,
        )
        return result

    return wrapper
