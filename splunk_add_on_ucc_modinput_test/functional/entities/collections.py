from typing import List, Dict, Tuple
from splunk_add_on_ucc_modinput_test.functional.entities.forge import FrameworkForge
from splunk_add_on_ucc_modinput_test.functional.entities.test import FrameworkTest
from splunk_add_on_ucc_modinput_test.functional.entities.task import FrameworkTask

class TestCollection(Dict[Tuple[str, str], FrameworkTest]):
    def add(self, item):
        assert isinstance(item, FrameworkTest)
        if item.key not in self:
            self[item.key] = item

    def lookup_by_function(self, fn):
        test = FrameworkTest(fn)
        if test.key in self:
            return super().__getitem__(test.key)
        return None

class ForgeCollection(Dict[Tuple[str, str, str], FrameworkForge]):
    def add(self, item: FrameworkForge):
        if item.key not in self:
            self[item.key] = item

    def lookup_by_function(self, fn):
        forge = FrameworkForge(fn)
        if forge.key in self:
            return super().__getitem__(forge.key)
        return None

class TaskCollection:
    def __init__(self):
        self._tasks_by_test = {}

    def remove_test_tasks(self, task_key):
        return self._tasks_by_test.pop(task_key, None)
        
    def add(self, tasks: List[FrameworkTask]):
        if not tasks:
            return
        test_key = tasks[0].test_key
        if test_key not in self._tasks_by_test:
            self._tasks_by_test[test_key] = []
        self._tasks_by_test[test_key].insert(0, tasks)
                
    def get_by_test(self, test_key):
        return self._tasks_by_test.get(test_key, [])    
    
    def enumerate_tasks(self, test_key):
        test_tasks = self._tasks_by_test.get(test_key, [])
        for i, parralel_tasks in enumerate(test_tasks):
            for j, task in enumerate(parralel_tasks):
                yield i, j, task
                
    def tasks_by_state(self, test_key):
        done, pending = [], []
        for _, _, task in self.enumerate_tasks(test_key):
            if task.is_executed:
                done.append(task)
            else:
                pending.append(task)
        return done, pending