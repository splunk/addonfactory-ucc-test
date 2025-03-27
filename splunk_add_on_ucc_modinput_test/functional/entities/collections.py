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
from splunk_add_on_ucc_modinput_test.typing import (
    ExecutableKeyType,
)


from typing import Any, Callable, Generator, List, Dict, Optional, Tuple
from splunk_add_on_ucc_modinput_test.functional.entities.forge import (
    FrameworkForge,
)
from splunk_add_on_ucc_modinput_test.functional.entities.test import (
    FrameworkTest,
)
from splunk_add_on_ucc_modinput_test.functional.entities.task import (
    FrameworkTask,
    TaskSetListType,
)
from splunk_add_on_ucc_modinput_test.functional import logger


class TestCollection(Dict[ExecutableKeyType, FrameworkTest]):
    @property
    def is_empty(self) -> bool:
        return not bool(self)

    def add(self, item: FrameworkTest) -> None:
        assert isinstance(item, FrameworkTest)
        if item.key not in self:
            self[item.key] = item

    def lookup_by_function(
        self, fn: Callable[..., Any]
    ) -> Optional[FrameworkTest]:
        test = FrameworkTest(fn)
        return self.get(test.key)

    def lookup_by_original_function(
        self, fn: Callable[..., Any]
    ) -> List[ExecutableKeyType]:
        found_tests_keys = set()
        lookup_test = FrameworkTest(fn)
        for key, test in self.items():
            if lookup_test.key == test.original_key:
                logger.debug(
                    f"lookup_by_original_function found key: \
                        {lookup_test.key} -> {test.key}|{test.original_key}"
                )
                found_tests_keys.add(key)

        return list(found_tests_keys)


class ForgeCollection(Dict[ExecutableKeyType, FrameworkForge]):
    @property
    def is_empty(self) -> bool:
        return not bool(self)

    def add(self, item: FrameworkForge) -> None:
        if item.key not in self:
            self[item.key] = item


class TaskCollection:
    def __init__(self) -> None:
        self._tasks: Dict[ExecutableKeyType, TaskSetListType] = {}

    @property
    def is_empty(self) -> bool:
        return not bool(self._tasks)

    def remove_test_tasks(
        self, test_key: ExecutableKeyType
    ) -> Optional[TaskSetListType]:
        return self._tasks.pop(test_key, None)

    def add(self, tasks: List[FrameworkTask]) -> None:
        if not tasks:
            return
        test_key = tasks[0].test_key
        if test_key not in self._tasks:
            self._tasks[test_key] = []
        self._tasks[test_key].append(tasks)

    def get_tasks_by_type(
        self, test_key: ExecutableKeyType
    ) -> Tuple[TaskSetListType, TaskSetListType]:
        all_tasks = self.get_tasks(test_key)
        inplace_tasks: TaskSetListType = []
        bootstrap_tasks: TaskSetListType = []
        for step_tasks in all_tasks:
            if step_tasks is not None:
                if step_tasks[0].is_bootstrap:
                    bootstrap_tasks.append(step_tasks)
                else:
                    inplace_tasks.append(step_tasks)
        return inplace_tasks, bootstrap_tasks

    def get_bootstrap_tasks(
        self, test_key: ExecutableKeyType
    ) -> TaskSetListType:
        all_tasks = self.get_tasks(test_key)
        bootstrap_tasks: TaskSetListType = []
        for t in all_tasks:
            if t is not None and t[0].is_bootstrap:
                bootstrap_tasks.append(t)
        logger.debug(f"get_bootstrap_tasks for {test_key}: {bootstrap_tasks}")
        return bootstrap_tasks

    def get_inplace_tasks(
        self, test_key: ExecutableKeyType
    ) -> TaskSetListType:
        all_tasks = self.get_tasks(test_key)
        inplace_tasks: TaskSetListType = []
        for t in all_tasks:
            if t is not None and not t[0].is_bootstrap:
                inplace_tasks.append(t)
        logger.debug(f"get_inplace_tasks for {test_key}: {inplace_tasks}")
        return inplace_tasks

    def get_tasks(self, test_key: ExecutableKeyType) -> TaskSetListType:
        tasks = self._tasks.get(test_key, [])
        logger.debug(f"get_tasks for {test_key}: {tasks}")
        return tasks

    def enumerate_tasks(
        self, test_key: Tuple[str, ...]
    ) -> Generator[Tuple[int, int, FrameworkTask], None, None]:
        test_tasks = self.get_tasks(test_key)
        for i, parralel_tasks in enumerate(test_tasks):
            if parralel_tasks is not None:
                for j, task in enumerate(parralel_tasks):
                    yield i, j, task

    def enumerate_bootstrap_tasks(
        self, test_key: ExecutableKeyType
    ) -> Generator[Tuple[int, int, FrameworkTask], None, None]:
        bootstrap_tasks = self.get_bootstrap_tasks(test_key)
        for i, parralel_tasks in enumerate(bootstrap_tasks):
            if parralel_tasks is not None:
                for j, task in enumerate(parralel_tasks):
                    yield i, j, task

    def enumerate_inplace_tasks(
        self, test_key: ExecutableKeyType
    ) -> Generator[Tuple[int, int, FrameworkTask], None, None]:
        inplace_tasks = self.get_inplace_tasks(test_key)
        for i, parralel_tasks in enumerate(inplace_tasks):
            if parralel_tasks is not None:
                for j, task in enumerate(parralel_tasks):
                    yield i, j, task

    def bootstrap_tasks_by_state(
        self, test_key: ExecutableKeyType
    ) -> Tuple[List[FrameworkTask], List[FrameworkTask]]:
        done, pending = [], []
        for _, _, task in self.enumerate_bootstrap_tasks(test_key):
            if task.is_executed:
                done.append(task)
            else:
                pending.append(task)
        return done, pending
