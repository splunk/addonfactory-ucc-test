import threading
import inspect
import contextlib
import time
from typing import Any, Dict, List, Type
from dataclasses import dataclass, replace
from splunk_add_on_ucc_modinput_test.functional import logger
from splunk_add_on_ucc_modinput_test.functional.entities.executable import (
    ExecutableBase,
)


@dataclass
class ForgeExecData:
    id: str
    teardown: object
    kwargs: Dict[str, Any]
    result: object
    errors: List[str]
    count: int
    lock: threading.Lock
    is_teardown_executed: bool = False

    def __init__(
        self,
        id: str,
        teardown: object,
        kwargs: Dict[str, Any],
        result: object,
        errors: List[str],
        count: int,
    ) -> None:
        self.lock = threading.Lock()
        self.id = id
        self.teardown = teardown
        self.kwargs = kwargs
        self.result = result
        self.errors = errors
        self.count = count

    def summary(self, offset: str = "") -> str:
        s = f"\n{offset}Teardown summary:"
        s += f"\n{offset}\tdata.id: {self.id},"
        s += f"\n{offset}\tdata.count={self.count},"
        s += f"\n{offset}\tdata.is_teardown_executed={self.is_teardown_executed}"
        s += f"\n{offset}\tdata.teardown={self.teardown}"
        s += f"\n{offset}\tdata.kwargs={self.kwargs}"
        s += f"\n{offset}\tdata.result={self.result}"
        return s


class ForgePostExec:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self._exec_store: Dict[str, Any] = {}
        self._teardown_is_blocked = False

    def summary(self, data: ForgeExecData) -> None:
        s = data.summary()
        s += f"\n\tteardown_is_blocked={self._teardown_is_blocked}"

    def block_teardown(self) -> None:
        self._teardown_is_blocked = True

    def unblock_teardown(self) -> None:
        self._teardown_is_blocked = False
        self.exec_ready_teardowns()

    def exec_ready_teardowns(self) -> None:
        for data in self._exec_store.values():
            self.exec_teardown_if_ready(data)

    def exec_teardown_if_ready(self, data: ForgeExecData) -> bool:
        with data.lock:
            can_execute = (
                data.count == 0
                and not self._teardown_is_blocked
                and not data.is_teardown_executed
            )
            logger.debug(
                f"CAN EXECUTE TEARDOWN {can_execute}:{self.summary(data)}"
            )
            if can_execute:
                self.execute_teardown(data)
        return can_execute

    def add(
        self,
        id: str,
        teardown: object,
        kwargs: dict,
        result: object,
        errors: List[str],
    ) -> None:
        if id not in self._exec_store:
            with self.lock:
                data = ForgeExecData(id, teardown, kwargs, result, errors, 1)
                self._exec_store[id] = data
            logger.debug(f"REGISTER TEARDOWN {id}: {self.summary(data)}")
        else:
            self.reuse(id)

    def get(self, id):
        data = self._exec_store.get(id)
        assert data
        return replace(data)

    def reuse(self, id):
        data = self._exec_store.get(id)
        assert data
        logger.debug(f"REUSE TEARDOWN {id}:{self.summary(data)}")
        with data.lock:
            data.count += 1

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
        if data is None:
            return False

        logger.debug(f"BEFORE EXECUTE TEARDOWN {id}:{self.summary(data)}")

        with data.lock:
            data.count -= 1

        teardown_start_time = time.time()
        executed = self.exec_teardown_if_ready(data)
        if executed:
            logger.info(
                f"Teardown has been executed successfully, time taken: {time.time() - teardown_start_time} seconds:{self.summary(data)}"
            )
        logger.debug(f"AFTER EXECUTE TEARDOWN {id}:{self.summary(data)}")
        return executed


class FrameworkForge(ExecutableBase):
    def __init__(self, function, scope: str):
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
    def scope(self):
        return self._scope

    @property
    def tests_keys(self):
        return list(self.tests)

    @property
    def name(self):
        return self.key[1]

    @property
    def path(self):
        return self.source_file

    @property
    def full_path(self):
        return "::".join(self.key[:2])

    @property
    def executions(self):
        return self._executions.list()

    def block_teardown(self):
        self._executions.block_teardown()

    def unblock_teardown(self):
        self._executions.unblock_teardown()

    def teardown(self, id):
        return self._executions.dereference_teardown(id)

    def register_execution(self, id, *, teardown, kwargs, result, errors):
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
