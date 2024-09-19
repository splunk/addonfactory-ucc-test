import time
import threading
import inspect
import contextlib
import types
from dataclasses import dataclass, replace
from splunk_add_on_ucc_modinput_test.functional import logger
from splunk_add_on_ucc_modinput_test.functional.constants import DEPENDENCIES_WAIT_TIMEOUT, BuiltInArg, ForgeProbe
from splunk_add_on_ucc_modinput_test.functional.exceptions import (
    SplTaFwkWaitForDependenciesTimeout,
    SplTaFwkDependencyExecutionError,
)
from splunk_add_on_ucc_modinput_test.functional.collections import FrmwkFunction, DependencyCollection, TestCollection
from splunk_add_on_ucc_modinput_test.functional.executor import FrmwkExecTask


class FrmwkTest(FrmwkFunction):
    def __init__(self, function, altered_name=None):
        super().__init__(function)
        self._dependencies = DependencyCollection()
        self._dep_exec_tasks = []
        self._is_executed = False
        self._artifacts = {}
        if altered_name:
            self._fn_name = altered_name

    @property
    def bound_deps(self):
        return self._dependencies.values()

    @property
    def dep_tasks(self):
        return self._dep_exec_tasks

    def flat_dep_tasks(self):
        for level, parralel_dep in enumerate(self._dep_exec_tasks):
            for index, dep in enumerate(parralel_dep):
                yield level, index, dep

    @property
    def is_executed(self):
        return self._is_executed

    @property
    def artifacts(self):
        return self._artifacts

    def update_artifacts(self, artifacts):
        assert isinstance(artifacts, dict)
        return self._artifacts.update(artifacts)

    def mark_executed(self):
        logger.debug(f"TEST: mark_executed {self}")
        self._is_executed = True

    def __contains__(self, dep):
        return dep in self._dependencies

    def link_dependency(self, dep_list, parametrize_kwargs={}):
        for dep, _, _ in dep_list:
            assert isinstance(dep, FrmwkDependency)
            assert dep.key not in self._dependencies
            self._dependencies[dep.key] = dep

        deps_tasks = []
        for dep, probe, kwargs in dep_list:
            dep_kwargs = kwargs.copy()
            dep_kwargs.update(parametrize_kwargs)
            deps_tasks.append(FrmwkExecTask(self, dep, dep_kwargs, probe))

        self._dep_exec_tasks.insert(0, deps_tasks)
        logger.debug(
            f"TEST: link_dependency {self}, tasks: {deps_tasks}, parametrize_kwargs: {parametrize_kwargs}"
        )

    def wait_for_dependencies(self):
        timeout = time.time() + DEPENDENCIES_WAIT_TIMEOUT
        while True:
            for _, _, task in self.executed_deps:
                if task.error:
                    dep_key = "::".join(task._dep.key[:2])
                    test_key = "::".join(self.key)
                    msg = f"Dependency {dep_key} failed to execute for test {test_key} with error: {task.error}"
                    logger.error(f"{msg}, call arguments:  {task._call_args}")
                    raise SplTaFwkDependencyExecutionError(msg)

            if self.all_deps_executed:
                break

            if time.time() > timeout:
                msg = f"{self} exceeted {DEPENDENCIES_WAIT_TIMEOUT} seconds timeout while waiting for dependencies: {self.not_executed_deps}"
                logger.error(msg)
                raise SplTaFwkWaitForDependenciesTimeout(msg)
            logger.debug(f"{self} is waiting for dependencies")
            time.sleep(1)
        logger.debug(f"{self} dependencies are ready")

    def __repr__(self):
        return f"<Test {'::'.join(self.key)}>"

    @property
    def all_deps_executed(self):
        return not self.not_executed_deps

    @property
    def not_executed_deps(self):
        not_executed = []
        logger.debug(f"TEST {self}, key: {self.key} not executed dep tasks")
        for i, j, dep_task in self.flat_dep_tasks():
            if not dep_task.is_executed:
                not_executed.append((i, j, dep_task))
                logger.debug(
                    f"TEST:    task {i}:{j}, {id(dep_task)} - {dep_task} - {dep_task.is_executed}, dep: {id(dep_task._dep)} - {dep_task._dep} - {dep_task._dep.key}"
                )
        return not_executed

    @property
    def executed_deps(self):
        return [
            (i, j, dep_task)
            for i, j, dep_task in self.flat_dep_tasks()
            if dep_task.is_executed
        ]

    def dump(self):
        logger.debug(f"TEST {self}, key: {self.key}")
        for i, j, task in self.flat_dep_tasks():
            logger.debug(
                f"TEST:    task {i}:{j}, {id(task)} - {task} - {task.is_executed}, dep: {id(task._dep)} - {task._dep} - {task._dep.key}"
            )

    def collect_required_kwargs(self, splunk_client=None, vendor_client=None):
        kwargs = {k: v for k, v in self._artifacts.items() if k in self._required_args}
        if splunk_client and BuiltInArg.SPLUNK_CLIENT.value in self._required_args:
            kwargs[BuiltInArg.SPLUNK_CLIENT.value] = splunk_client
        if vendor_client and BuiltInArg.VENDOR_CLIENT.value in self._required_args:
            kwargs[BuiltInArg.VENDOR_CLIENT.value] = vendor_client
        logger.debug(
            f"Finish collect_required_kwargs for test {self.key}: kwargs={kwargs}"
        )
        return kwargs


@dataclass
class ForgeExecution:
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
            data = ForgeExecution(id, teardown, kwargs, result, 1)
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


class FrmwkDependency(FrmwkFunction):
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
        id = prev_exec._id if isinstance(prev_exec, ForgeExecution) else prev_exec
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
        assert isinstance(test, FrmwkTest)
        return self._tests.pop(test.key, None)

    def link_test(self, test):
        assert isinstance(test, FrmwkTest)
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
