import threading
import inspect
import contextlib
from typing import List
from dataclasses import dataclass, replace
from splunk_add_on_ucc_modinput_test.functional import logger
from splunk_add_on_ucc_modinput_test.functional.entities.executable import (
    ExecutableBase,
)


@dataclass
class ForgeExecData:
    id: str
    teardown: object
    kwargs: dict
    result: object
    errors: List[str]
    count: int
    lock = threading.Lock
    is_teardown_executed: bool = False

    def __init__(self, id, teardown, kwargs, result, errors, count):
        self.lock = threading.Lock()
        self.id = id
        self.teardown = teardown
        self.kwargs = kwargs
        self.result = result
        self.errors = errors
        self.count = count


class ForgePostExec:
    def __init__(self):
        self.lock = threading.Lock()
        self._exec_store = {}
        self._teardown_is_blocked = False

    def block_teardown(self):
        self._teardown_is_blocked = True

    def unblock_teardown(self):
        self._teardown_is_blocked = False

    def add(self, id, teardown, kwargs, result, errors):
        if id not in self._exec_store:
            self.lock.acquire()
            try:
                data = ForgeExecData(id, teardown, kwargs, result, errors, 1)
                self._exec_store[id] = data
            finally:
                self.lock.release()
            logger.debug(
                f"REGISTER TEARDOWN {id}:\n\tdata.id: {data.id}\n\tdata.count={data.count},\n\tdata.is_teardown_executed={data.is_teardown_executed}\n\tdata.teardown={data.teardown}\n\tdata.kwargs={data.kwargs}\n\tdata.result={data.result}"
            )
        else:
            self.reuse(id)

    def get(self, id):
        data = self._exec_store.get(id)
        assert data
        return replace(data)

    def reuse(self, id):
        data = self._exec_store.get(id)
        assert data
        logger.debug(
            f"REUSE TEARDOWN {id}:\n\tdata.id: {data.id}\n\tdata.count={data.count},\n\tdata.is_teardown_executed={data.is_teardown_executed}\n\tdata.teardown={data.teardown}\n\tdata.kwargs={data.kwargs}\n\tdata.result={data.result}"
        )
        data.lock.acquire()
        data.count += 1
        data.lock.release()

    def get_teardown(self, id):
        data = self._exec_store.get(id)
        assert data
        return data.teardown

    def get_result(self, id):
        data = self._exec_store.get(id)
        assert data
        return data.result

    def get_count(self, id):
        data = self._exec_store.get(id)
        assert data
        return data.count

    def is_teardown_executed(self, id):
        data = self._exec_store.get(id)
        assert data
        return data.is_teardown_executed

    def list(self):
        return tuple(self._exec_store.values())

    def execute_teardown(self, data):
        teardown = data.teardown
        if inspect.isgenerator(teardown):
            with contextlib.suppress(StopIteration):
                next(teardown)
        elif callable(teardown):
            teardown()
        else:
            pass
        data.is_teardown_executed = True

    def dereference_teardown(self, id):
        data = self._exec_store.get(id)
        assert data
        logger.debug(
            f"BEFORE EXECUTE TEARDOWN {id}:\n\t_teardown_is_blocked={self._teardown_is_blocked}\n\tdata.id: {data.id}\n\tdata.count={data.count},\n\tdata.is_teardown_executed={data.is_teardown_executed}\n\tdata.teardown={data.teardown}\n\tdata.kwargs={data.kwargs}\n\tdata.result={data.result}"
        )
        data.lock.acquire()
        try:
            data.count -= 1
            if (
                data.count == 0
                and not self._teardown_is_blocked
                and not data.is_teardown_executed
            ):
                self.execute_teardown(data)
        finally:
            data.lock.release()
        logger.debug(
            f"AFTER EXECUTE TEARDOWN {id}:\n\tdata.id: {data.id}\n\tdata.count={data.count},\n\tdata.is_teardown_executed={data.is_teardown_executed}\n\tdata.teardown={data.teardown}\n\tdata.kwargs={data.kwargs}\n\tdata.result={data.result}"
        )


class FrameworkForge(ExecutableBase):
    def __init__(self, function, scope):
        super().__init__(function)
        self._scope = scope
        self.tests = set()
        self._executions = ForgePostExec()

    @property
    def key(self):
        key_value = list(super().key)
        key_value.append(self._scope)
        return tuple(key_value)

    def set_scope(self, scope):
        self._scope = scope

    @property
    def executions(self):
        return self._executions.list()

    def block_teardown(self):
        self._executions.block_teardown()

    def unblock_teardown(self):
        self._executions.unblock_teardown()

    def teardown(self, id):
        self._executions.dereference_teardown(id)

    def register_execution(self, id, teardown, kwargs, result, errors):
        self._executions.add(id, teardown, kwargs, result, errors)

    def reuse_execution(self, prev_exec):
        id = (
            prev_exec._id
            if isinstance(prev_exec, ForgeExecData)
            else prev_exec
        )
        self._executions.reuse(id)

    @property
    def is_executed(self):
        return self._is_executed

    def __contains__(self, test_key):
        return test_key in self.tests

    def unlink_test(self, test_key):
        self.tests.discard(test_key)

    def link_test(self, test_key):
        if test_key not in self.tests:
            self.tests.add(test_key)

    def __repr__(self):
        s = repr(self._function)
        return s.replace("<function", "<dependency function")
