import time
from dataclasses import dataclass, replace
from splunk_add_on_ucc_modinput_test.functional import logger
from splunk_add_on_ucc_modinput_test.functional.constants import DEPENDENCIES_WAIT_TIMEOUT, BuiltInArg
from splunk_add_on_ucc_modinput_test.functional.exceptions import (
    SplTaFwkWaitForDependenciesTimeout,
    SplTaFwkDependencyExecutionError,
)
from splunk_add_on_ucc_modinput_test.functional.entities.executable import ExecutableBase
from splunk_add_on_ucc_modinput_test.functional.entities.task import FrameworkTask
from splunk_add_on_ucc_modinput_test.functional.entities.collections import DependencyCollection
class FrameworkTest(ExecutableBase):
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
            assert isinstance(dep, ExecutableBase)
            assert dep.key not in self._dependencies
            self._dependencies[dep.key] = dep

        deps_tasks = []
        for dep, probe, kwargs in dep_list:
            dep_kwargs = kwargs.copy()
            dep_kwargs.update(parametrize_kwargs)
            deps_tasks.append(FrameworkTask(self, dep, dep_kwargs, probe))

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
