#
# Copyright 2025 Splunk Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import functools
from splunk_add_on_ucc_modinput_test.common import utils
from splunk_add_on_ucc_modinput_test.common import splunk_instance
from tests.modinput_functional.ta import Configuration as TaConfiguration
import logging
from typing import Callable
from mypy_extensions import NamedArg

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
) -> Callable[[NamedArg(TaConfiguration, "configuration")], None]:
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
