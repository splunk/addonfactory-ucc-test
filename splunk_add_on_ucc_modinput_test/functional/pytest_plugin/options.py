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
from argparse import ArgumentTypeError
from splunk_add_on_ucc_modinput_test.functional.constants import (
    ForgeProbe,
    TasksWait,
    Executor,
)
from pytest import Parser

from typing import Callable, Union


def int_range(min: int, max: int) -> Callable[[Union[int, str]], int]:
    def int_range_validator(value: Union[int, str]) -> int:
        try:
            value = int(value)
            assert min <= value <= max
        except Exception as e:
            err = f'Invalid value "{value}". Expected integer value in \
                inclusive range [{min}, {max}]'
            raise ArgumentTypeError(err) from e
        return value

    return int_range_validator


def pytest_addoption(parser: Parser) -> None:
    splunk_group = parser.getgroup(
        "addonfactory-ucc-test/functional - Options for unified functional \
            test framework for Splunk technical add-ons"
    )

    splunk_group.addoption(
        "--sequential-execution",
        dest="sequential_execution",
        action="store_true",
        default=False,
        help="Use no threading (for debugging).",
    )

    splunk_group.addoption(
        "--do-not-fail-with-teardown",
        dest="do_not_fail_with_teardown",
        action="store_true",
        default=False,
        help="Do not fail test if test's teardown fails. By default a test \
            will fail if any of its forges teardowns fail, even if the test \
                itself passed.",
    )

    splunk_group.addoption(
        "--do-not-delete-at-teardown",
        dest="do_not_delete_at_teardown",
        action="store_true",
        default=False,
        help="Do not delete created resoueces at teardown. This flag is for \
            debug purposes. Based on this flag developers can add alternative \
                code to forges, that, for example, would disable imputs \
                    instead of deletng them in order to study inputs after \
                        tests execution.",
    )

    allowed_range = [
        Executor.MIN_THREAD_NUMBER.value,
        Executor.MAX_THREAD_NUMBER.value,
    ]
    default = Executor.DEFAULT_THREAD_NUMBER.value
    splunk_group.addoption(
        "--number-of-threads",
        dest="number_of_threads",
        type=int_range(*allowed_range),
        default=10,
        help=f"Number of threads to use to execute forges. Allowed range: \
            {allowed_range}. Default value: {default}.",
    )

    allowed_range = [
        ForgeProbe.MIN_INTERVAL.value,
        ForgeProbe.MAX_INTERVAL.value,
    ]
    default = ForgeProbe.DEFAULT_INTERVAL.value
    splunk_group.addoption(
        "--probe-invoke-interval",
        dest="probe_invoke_interval",
        type=int_range(*allowed_range),
        default=default,
        help=f"Interval in seconds used to repeat invocation of yes/no type of \
            probe. Allowed range: {allowed_range}. Default value: {default}.",
    )

    allowed_range = [
        ForgeProbe.MIN_WAIT_TIME.value,
        ForgeProbe.MAX_WAIT_TIME.value,
    ]
    default = ForgeProbe.DEFAILT_WAIT_TIME.value
    splunk_group.addoption(
        "--probe-wait-timeout",
        dest="probe_wait_timeout",
        type=int_range(*allowed_range),
        default=default,
        help=f"Maximum time in seconds given to single probe to turn positive. \
            Allowed range: {allowed_range}. Default value: {default}.",
    )

    allowed_range = [
        TasksWait.MIN_BOOTSTRAP_TIMEOUT.value,
        TasksWait.MAX_BOOTSTRAP_TIMEOUT.value,
    ]
    default = TasksWait.DEFAULT_BOOTSTRAP_TIMEOUT.value
    splunk_group.addoption(
        "--bootstrap-wait-timeout",
        dest="bootstrap_wait_timeout",
        type=int_range(*allowed_range),
        default=default,
        help=f"Maximum time in seconds given to all bootstrap tasks to finish. \
            Allowed range: {allowed_range}. Default value: {default}.",
    )

    allowed_range = [
        TasksWait.MIN_ATTACHED_TIMEOUT.value,
        TasksWait.MAX_ATTACHED_TIMEOUT.value,
    ]
    default = TasksWait.DEFAULT_ATTACHED_TIMEOUT.value
    splunk_group.addoption(
        "--attached-tasks-wait-timeout",
        dest="attached_tasks_wait_timeout",
        type=int_range(*allowed_range),
        default=default,
        help=f"Maximum time in seconds given to finish all tasks attached to \
            a test. Allowed range: {allowed_range}. Default value: {default}.",
    )

    allowed_range = [
        TasksWait.MIN_CHECK_FREQUENCY.value,
        TasksWait.MAX_CHECK_FREQUENCY.value,
    ]
    default = TasksWait.DEFAULT_CHECK_FREQUENCY.value
    splunk_group.addoption(
        "--completion-check-frequency",
        dest="completion_check_frequency",
        type=int_range(*allowed_range),
        default=default,
        help=f"Frequency to check that bootstrap or attached tasks bundle has \
            finished to execute. Allowed range: {allowed_range}. \
                Default value: {default}.",
    )
