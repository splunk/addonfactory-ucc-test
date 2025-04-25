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
from typing import Optional
from pytest import Config
from splunk_add_on_ucc_modinput_test.functional.constants import (
    Executor,
    ForgeProbe,
    TasksWait,
)


class PytestConfigAdapter:
    def __init__(self, pytest_config: Optional[Config] = None) -> None:
        self._pytest_config = pytest_config

    def link_pytest_config(
        self, pytest_config: Optional[Config] = None
    ) -> None:
        self._pytest_config = pytest_config

    @property
    def pytest_config(self) -> Optional[Config]:
        return self._pytest_config

    @property
    def do_not_fail_with_teardown(self) -> bool:
        if self._pytest_config is not None:
            return self._pytest_config.getvalue("do_not_fail_with_teardown")
        return False

    @property
    def sequential_execution(self) -> bool:
        if self._pytest_config is not None:
            return self._pytest_config.getvalue("sequential_execution")
        return False

    @property
    def number_of_threads(self) -> int:
        if self._pytest_config is not None:
            return self._pytest_config.getvalue("number_of_threads")
        return Executor.DEFAULT_THREAD_NUMBER.value

    @property
    def probe_invoke_interval(self) -> int:
        if self._pytest_config is not None:
            return self._pytest_config.getvalue("probe_invoke_interval")
        return ForgeProbe.DEFAULT_INTERVAL.value

    @property
    def probe_wait_timeout(self) -> int:
        if self._pytest_config is not None:
            return self._pytest_config.getvalue("probe_wait_timeout")
        return ForgeProbe.DEFAILT_WAIT_TIME.value

    @property
    def bootstrap_wait_timeout(self) -> int:
        if self._pytest_config is not None:
            return self._pytest_config.getvalue("bootstrap_wait_timeout")
        return TasksWait.DEFAULT_BOOTSTRAP_TIMEOUT.value

    @property
    def attached_tasks_wait_timeout(self) -> int:
        if self._pytest_config is not None:
            return self._pytest_config.getvalue("attached_tasks_wait_timeout")
        return TasksWait.DEFAULT_ATTACHED_TIMEOUT.value

    @property
    def completion_check_frequency(self) -> int:
        if self._pytest_config is not None:
            return self._pytest_config.getvalue("completion_check_frequency")
        return TasksWait.DEFAULT_CHECK_FREQUENCY.value

    @property
    def do_not_delete_at_teardown(self) -> bool:
        if self._pytest_config is not None:
            return self._pytest_config.getvalue("do_not_delete_at_teardown")
        return False

    @property
    def collectonly(self) -> bool:
        if self._pytest_config is not None:
            return self._pytest_config.getvalue("collectonly")
        return False
