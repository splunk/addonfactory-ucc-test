import threading
import inspect
import contextlib
from dataclasses import dataclass, replace
from splunk_add_on_ucc_modinput_test.functional import logger
from splunk_add_on_ucc_modinput_test.functional.entities.executable import ExecutableBase
from splunk_add_on_ucc_modinput_test.functional.entities.collections import TestCollection
@dataclass
class ForgeExecData:
    id: str
    teardown: object
    kwargs: dict
    result: object
    count: int
    lock = threading.Lock
    is_teardown_executed: bool = False

    def __post_init__(self):
        self.lock = threading.Lock()


class ForgePostExec:
    def __init__(self):
        self.lock = threading.Lock()
        self._exec_store = {}

    def add(self, id, teardown, kwargs, result):
        if id not in self._exec_store:
            self.lock.acquire()
            data = ForgeExecData(id, teardown, kwargs, result, 1)
            self._exec_store[id] = data
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

    def execute_teardown(self, id):
        data = self._exec_store.get(id)
        assert data
        logger.debug(
            f"BEFORE EXECUTE TEARDOWN {id}:\n\tdata.id: {data.id}\n\tdata.count={data.count},\n\tdata.is_teardown_executed={data.is_teardown_executed}\n\tdata.teardown={data.teardown}\n\tdata.kwargs={data.kwargs}\n\tdata.result={data.result}"
        )
        data.lock.acquire()
        try:
            data.count -= 1
            if data.count == 0 and not data.is_teardown_executed:
                teardown = data.teardown
                if inspect.isgenerator(teardown):
                    with contextlib.suppress(StopIteration):
                        next(teardown)
                elif callable(teardown):
                    teardown()
                else:
                    pass
                data.is_teardown_executed = True
        finally:
            data.lock.release()
        logger.debug(
            f"AFTER EXECUTE TEARDOWN {id}:\n\tdata.id: {data.id}\n\tdata.count={data.count},\n\tdata.is_teardown_executed={data.is_teardown_executed}\n\tdata.teardown={data.teardown}\n\tdata.kwargs={data.kwargs}\n\tdata.result={data.result}"
        )


class FrameworkForge(ExecutableBase):
    def __init__(self, function, scope):
        super().__init__(function)
        self._scope = scope
        self._tests = TestCollection()
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

    def teardown(self, id):
        self._executions.execute_teardown(id)

    def register_execution(self, id, teardown, kwargs, result):
        self._executions.add(id, teardown, kwargs, result)

    def reuse_execution(self, prev_exec):
        id = prev_exec._id if isinstance(prev_exec, ForgeExecData) else prev_exec
        self._executions.reuse(id)

    @property
    def bound_tests(self):
        return self._tests.values()

    @property
    def is_executed(self):
        return self._is_executed

    def __contains__(self, test):
        return test in self._tests

    def unlink_test(self, test):
        return self._tests.pop(test.key, None)

    def link_test(self, test):
        assert isinstance(test, ExecutableBase)
        if test.key not in self._tests:
            self._tests[test.key] = test

    def __repr__(self):
        s = repr(self._function)
        return s.replace("<function", f"<dependency function")

    @property
    def all_tests_executed(self):
        return not self.not_executed_tests

    @property
    def not_executed_tests(self):
        return [test for test in self.bound_tests if not test.is_executed]

    @property
    def executed_deps(self):
        return [test for test in self.bound_tests if test.is_executed]
