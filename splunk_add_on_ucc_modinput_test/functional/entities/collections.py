from typing import List, Dict, Tuple
from splunk_add_on_ucc_modinput_test.functional.entities.forge import (
    FrameworkForge,
)
from splunk_add_on_ucc_modinput_test.functional.entities.test import (
    FrameworkTest,
)
from splunk_add_on_ucc_modinput_test.functional.entities.task import (
    FrameworkTask,
)
from splunk_add_on_ucc_modinput_test.functional import logger


class TestCollection(Dict[Tuple[str, str], FrameworkTest]):
    @property
    def is_empty(self):
        return not bool(self)
    
    def add(self, item):
        assert isinstance(item, FrameworkTest)
        if item.key not in self:
            self[item.key] = item

    def lookup_by_function(self, fn):
        test = FrameworkTest(fn)
        return self.get(test.key)


    def lookup_by_original_function(self, fn):
        found_tests_keys = set()
        lookup_test = FrameworkTest(fn)
        for key, test in self.items():
            if lookup_test.key == test.original_key:
                logger.debug(f"lookup_by_original_function found key: {lookup_test.key} -> {test.key}|{test.original_key}")
                found_tests_keys.add(key)
                
        return list(found_tests_keys)

class ForgeCollection(Dict[Tuple[str, str, str], FrameworkForge]):
    @property
    def is_empty(self):
        return not bool(self)

    def add(self, item: FrameworkForge):
        if item.key not in self:
            self[item.key] = item

    def lookup_by_function(self, fn):
        forge = FrameworkForge(fn)
        return self.get(forge.key)


class TaskCollection:
    def __init__(self):
        self._tasks = {}

    @property
    def is_empty(self):
        return not bool(self._tasks)
    
    def remove_test_tasks(self, test_key):
        return self._tasks.pop(test_key, None)

    def add(self, tasks: List[FrameworkTask]):
        if not tasks:
            return
        test_key = tasks[0].test_key
        if test_key not in self._tasks:
            self._tasks[test_key] = []
        self._tasks[test_key].append(tasks)

    def get_tasks_by_type(self, test_key):
        all_tasks = self.get_tasks(test_key)
        inplace_tasks, bootstrap_tasks = [], []
        for step_tasks in all_tasks:
            if step_tasks[0].is_bootstrap:
                bootstrap_tasks.append(step_tasks)
            else:
                inplace_tasks.append(step_tasks)
        return inplace_tasks, bootstrap_tasks

    def get_bootstrap_tasks(self, test_key):
        all_tasks = self.get_tasks(test_key)
        if all_tasks:
            bootstrap_tasks = [t for t in all_tasks if t[0].is_bootstrap]
        else:
            bootstrap_tasks = []
        logger.debug(f"get_bootstrap_tasks for {test_key}: {bootstrap_tasks}")
        return bootstrap_tasks

    def get_inplace_tasks(self, test_key):
        all_tasks = self.get_tasks(test_key)
        if all_tasks:
            inplace_tasks = [t for t in all_tasks if not t[0].is_bootstrap]
        else:
            inplace_tasks = []
        logger.debug(f"get_inplace_tasks for {test_key}: {inplace_tasks}")
        return inplace_tasks

    def get_tasks(self, test_key):
        tasks = self._tasks.get(test_key, [])
        logger.debug(f"get_tasks for {test_key}: {tasks}")
        return tasks

    def enumerate_tasks(self, test_key):
        test_tasks = self.get_tasks(test_key)
        for i, parralel_tasks in enumerate(test_tasks):
            for j, task in enumerate(parralel_tasks):
                yield i, j, task

    def enumerate_bootstrap_tasks(self, test_key):
        bootstrap_tasks = self.get_bootstrap_tasks(test_key)
        for i, parralel_tasks in enumerate(bootstrap_tasks):
            for j, task in enumerate(parralel_tasks):
                yield i, j, task

    def enumerate_inplace_tasks(self, test_key):
        inplace_tasks = self.get_inplace_tasks(test_key)
        for i, parralel_tasks in enumerate(inplace_tasks):
            for j, task in enumerate(parralel_tasks):
                yield i, j, task

    def bootstrap_tasks_by_state(self, test_key):
        done, pending = [], []
        for _, _, task in self.enumerate_bootstrap_tasks(test_key):
            if task.is_executed:
                done.append(task)
            else:
                pending.append(task)
        return done, pending
