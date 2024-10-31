import time
import random
import string
from typing import List, Tuple, Optional, Union
from splunk_add_on_ucc_modinput_test.functional import logger
from splunk_add_on_ucc_modinput_test.functional.exceptions import (
    SplTaFwkDependencyExecutionError,
    SplTaFwkWaitForDependenciesTimeout,
)
from splunk_add_on_ucc_modinput_test.functional.constants import (
    ForgeScope,
    TasksWait,
)
from splunk_add_on_ucc_modinput_test.functional.entities import (
    TestCollection,
    ForgeCollection,
    TaskCollection,
    FrameworkTest,
    FrameworkForge,
    FrameworkTask,
)
from splunk_add_on_ucc_modinput_test.functional.executor import (
    FrmwkParallelExecutor,
    FrmwkSequentialExecutor,
)
from splunk_add_on_ucc_modinput_test.functional.splunk import (
    SplunkClientBase,
    SplunkConfigurationBase,
)
from splunk_add_on_ucc_modinput_test.common import splunk_instance
from splunk_add_on_ucc_modinput_test.functional.vendor import (
    VendorClientBase,
    VendorConfigurationBase,
)

from splunk_add_on_ucc_modinput_test.functional.constants import BuiltInArg
from splunk_add_on_ucc_modinput_test.functional.common.pytest_config_adapter import PytestConfigAdapter
from splunk_add_on_ucc_modinput_test.functional.common.identifier_factory import (
    create_identifier,
    IdentifierType
)

class forge:
    def __init__(
        self,
        forge_fn,
        *,
        probe=None,
        scope: Optional[Union[ForgeScope, str]] = None,
        **kwargs,
    ):
        self.forge_fn = forge_fn
        self.probe = probe
        self.scope = scope.value if isinstance(scope, ForgeScope) else scope
        self.kwargs = kwargs


class forges:
    def __init__(
        self, *forge_list, scope: Optional[Union[ForgeScope, str]] = None
    ):
        self.forge_list = forge_list
        self.scope = scope.value if isinstance(scope, ForgeScope) else scope


class TestDependencyManager(PytestConfigAdapter):
    def __init__(self):
        super().__init__()
        self.tests = TestCollection()
        self.forges = ForgeCollection()
        self.tasks = TaskCollection()
        self.executor = None
        self._vendor_clients = {BuiltInArg.VENDOR_CLIENT.value: (VendorClientBase, VendorConfigurationBase)}
        self._splunk_clients = {BuiltInArg.SPLUNK_CLIENT.value: (SplunkClientBase, SplunkConfigurationBase)}
        self._pytest_config = None
        self._session_id = self.generate_session_id()
        self._global_builtin_args_pool = {}

    @staticmethod
    def generate_session_id():
        return create_identifier(id_type=IdentifierType.ALPHA, in_uppercase=True)

    def set_vendor_client_class(self, vendor_configuration_class, vendor_client_class, vendor_class_argument_name):
        logger.debug(f"set_vendor_client_class: {vendor_client_class}, {vendor_configuration_class}, {vendor_class_argument_name}")
        assert issubclass(vendor_client_class, VendorClientBase)
        assert issubclass(vendor_configuration_class, VendorConfigurationBase)
        self._vendor_clients[vendor_class_argument_name] = (vendor_client_class, vendor_configuration_class)

    def create_vendor_client(self):
        return self._vendor_client_class()

    def set_splunk_client_class(self, splunk_configuration_class, splunk_client_class, splunk_class_argument_name):
        logger.debug(f"set_splunk_client_class: {splunk_configuration_class}, {splunk_client_class}, {splunk_class_argument_name}")
        assert issubclass(splunk_client_class, SplunkClientBase)
        assert issubclass(splunk_configuration_class, SplunkConfigurationBase)
        self._splunk_clients[splunk_class_argument_name] = (splunk_client_class, splunk_configuration_class)

    def create_splunk_client(self):
        return self._splunk_client_class()

    def create_global_builtin_args(self):
        global_builtin_args = {
            BuiltInArg.SESSION_ID.value: self.session_id,
        }
        
        for prop, (client, config) in self._vendor_clients.items():
            global_builtin_args[prop] = client(config(self._pytest_config))
        
        for prop, (client, config) in self._splunk_clients.items():
            global_builtin_args[prop] = client(config(self._pytest_config))
            
        return global_builtin_args
                    
    def get_global_builtin_args(self, test_key):
        if test_key not in self._global_builtin_args_pool:
            self._global_builtin_args_pool[test_key] = self.create_global_builtin_args()
        
        return self._global_builtin_args_pool[test_key]
        
    @property
    def session_id(self):
        return self._session_id

    def _interpret_scope(
        self, scope: Optional[str], test: FrameworkTest
    ) -> Optional[str]:
        if scope is None:
            return None

        if scope == ForgeScope.FUNCTION.value:
            scope = "::".join(test.key)
        elif scope == ForgeScope.MODULE.value:
            scope = test.source_file

        return scope

    def bind(self, test_fn, scope, frg_fns, is_bootstrap):
        logger.debug(f"bind: {test_fn} -> {frg_fns}")

        test = self.tests.lookup_by_function(test_fn)
        if not test:
            test = FrameworkTest(test_fn)
            self.tests.add(test)

        frg_group_scope = self._interpret_scope(scope, test)

        frg_list = []
        for f in frg_fns:
            if frg_group_scope is None and f.scope is None:
                frg_scope = ForgeScope.SESSION.value
            elif f.scope is not None:
                frg_scope = self._interpret_scope(f.scope, test)
            else:
                frg_scope = frg_group_scope

            frg = FrameworkForge(f.forge_fn, frg_scope)
            found = self.forges.get(frg.key)
            if not found:
                self.forges.add(frg)
                logger.debug(
                    f"BIND created frg {id(frg)} - {frg} - {frg.key}, is_bootstrap: {is_bootstrap}"
                )
            else:
                frg = found
                logger.debug(
                    f"BIND found frg {id(frg)} - {frg} - {frg.key}, is_bootstrap: {is_bootstrap}"
                )

            frg_list.append(
                FrameworkTask(test, frg, is_bootstrap, f.kwargs, f.probe)
            )

            frg.link_test(test.key)
            test.link_forge(frg.key)

        self.tasks.add(frg_list)

        return test

    def unregister_test(self, test_key):
        test = self.tests.pop(test_key, None)
        if test:
            for frg_key in test.forges:
                frg = self.forges.get(frg_key)
                if frg:
                    frg.unlink_test(test.key)
        return test

    def find_test(self, test_fn, parametrized_name):
        test_obj = FrameworkTest(test_fn, parametrized_name)
        return self.tests.get(test_obj.key)

    def dump_tests(self):
        logger.debug(f"DUMP TESTS: {len(self.tests.items())}")
        for key, test in self.tests.items():
            logger.debug(f"test key:{key} value: {test}")

    def copy_task_for_parametrized_test(self, test, kwargs, src_task):
        frg = src_task._forge
        frg.link_test(test.key)
        test.link_forge(frg.key)
        probe = src_task.get_probe_fn()
        is_bootstrap = src_task.is_bootstrap
        kwargs = src_task.get_forge_kwargs_copy()
        kwargs.update(kwargs)
        return FrameworkTask(test, frg, is_bootstrap, kwargs, probe)

    def expand_parametrized_tests(self, parametrized_tests):
        for test_key, param_tests in parametrized_tests.items():
            test = self.unregister_test(test_key)
            if not test:
                logger.debug(f"TEST NOT FOUND: {test.key}")
                continue

            logger.debug(f"Test found: {test.key}")
            test_tasks = self.tasks.remove_test_tasks(test_key)
            assert test_tasks
            for test_name, parametrized_kwargs in param_tests:
                logger.debug(
                    f"adding test: {test.key} => test_name: {test_name}, kwargs: {parametrized_kwargs}"
                )
                parametrized_test = FrameworkTest(test._function, test_name)
                logger.debug(
                    f"create parametrized test: {parametrized_test.key}, {vars(parametrized_test)}"
                )
                self.tests.add(parametrized_test)

                for parallel_tasks in test_tasks[::-1]:
                    frg_list = []
                    for src_task in parallel_tasks:
                        parametrized_task = (
                            self.copy_task_for_parametrized_test(
                                parametrized_test,
                                parametrized_kwargs,
                                src_task,
                            )
                        )
                        frg_list.append(parametrized_task)

                    self.tasks.add(frg_list)

                    logger.debug(
                        f"parametrized_test.link_forge: {parametrized_test.key}: {frg_list} => {parametrized_test}"
                    )

    def _log_dep_exec_matrix(self, tests, dep_mtx):
        matrix = "\nBootstrap Dependency execution matrix:\n"
        for step_index, group in enumerate(dep_mtx):
            matrix += f"Step {step_index}:\n"
            for test_index, test_tasks in enumerate(group):
                matrix += f"\ttest: {'::'.join(tests[test_index].key)}\n"
                if test_tasks is not None:
                    for task in test_tasks:
                        matrix += f"\t\tDependency {task.forge_full_path}, scope {task.forge_scope}\n"
                else:
                    matrix += "\t\tNo depemdemcies at this step\n"
        logger.info(matrix)

    def remove_skipped_tests(self, skipped_tests_keys):
        for test_key in skipped_tests_keys:
            self.unregister_test(test_key)

    def synch_tests_with_pytest_list(self, pytest_test_set_keys):
        tests_to_remove = [
            test_key
            for test_key in self.tests.keys()
            if test_key not in pytest_test_set_keys
        ]
        self.remove_skipped_tests(tests_to_remove)

    def build_bootstrap_matrix(self):
        tests = list(self.tests.values())

        exec_steps = []
        step_index = 0
        while True:
            step_tasks = [None] * len(tests)
            for pos, test in enumerate(tests):
                tasks = self.tasks.get_bootstrap_tasks(test.key)
                if step_index < len(tasks):
                    step_tasks[pos] = tasks[step_index]
            if not any(step_tasks):
                break
            exec_steps.append(step_tasks)
            step_index += 1

        self._log_dep_exec_matrix(tests, exec_steps)
        return exec_steps

    def start_bootstrap_execution(self):
        if self.tasks.is_empty:
            return

        logger.info("Starting bootstrap forges execution.")
        if self.executor is None:
            if self.sequential_execution:
                self.executor = FrmwkSequentialExecutor(self)
            else:
                self.executor = FrmwkParallelExecutor(
                    self, self.number_of_threads
                )

        deps_exec_mtx = dependency_manager.build_bootstrap_matrix()
        if deps_exec_mtx:
            self._execution_timeout = time.time() + TasksWait.TIMEOUT.value
            self.executor.start(deps_exec_mtx)

    def inplace_tasks_execution(self, deps_exec_mtx):
        logger.debug(f"start inplace_tasks_execution:{deps_exec_mtx}")
        if not deps_exec_mtx:
            return
        assert self.executor is not None
        logger.debug("inplace_tasks_execution is about to start")
        self._execution_timeout = time.time() + TasksWait.TIMEOUT.value
        self.executor.start(deps_exec_mtx)
        self.executor.wait()

    def shutdown(self):
        logger.info("Shutting down dependency manager...")

        if self.executor is not None:
            self.executor.shutdown()

    def check_all_tests_executed(self):
        executed = [test.is_executed for test in self.tests.values()]
        return all(executed)

    def check_tests_executed(self, tests_keys: List[Tuple[str, ...]]):
        executed = [
            self.tests.get(test_key).is_executed for test_key in tests_keys
        ]
        return all(executed)

    def try_to_unblock_inplace_teardowns(self, test):
        inplace_tasks = self.tasks.enumerate_inplace_tasks(test.key)
        for _, _, task in inplace_tasks:
            if self.check_tests_executed(task.forge_test_keys):
                task.unblock_forge_teardown()

    def teardown_test_dependencies(self, test):
        self.try_to_unblock_inplace_teardowns(test)
        tasks = list(self.tasks.enumerate_tasks(test.key))
        for _, _, task in reversed(tasks):
            task.teardown()

    def teardown_test(self, test):
        logger.debug(f"teardown test:{test}")
        test.mark_executed()
        self.teardown_test_dependencies(test)

    def _check_failed_tasks(self, test, done_tasks):
        failed_tasks = [task.forge_key for task in done_tasks if task._errors]
        logger.debug(
            f"DONE TASKS for {test.key}: {[task.forge_key for task in done_tasks]}"
        )
        logger.debug(f"FAILED TASKS for {test.key}: {failed_tasks}")
        for task in done_tasks:
            if task.failed:
                test_path = "::".join(test.key)
                msg = f"Dependency {task.forge_full_path} failed to execute for test {test_path} with error:\n{task.error}"
                logger.error(msg)
                raise SplTaFwkDependencyExecutionError(msg)

    def _report_timeout(self, test, pending_tasks):
        msg = f"{test} exceeded {TasksWait.TIMEOUT.value} seconds timeout while waiting for dependencies:"
        for task in pending_tasks:
            msg += f"\n\t{task.forge_full_path}, self id: {id(task)}, scope: {task.forge_scope}, exec_id: {task._exec_id} is_executed: {task.is_executed}, is_failed: {task.failed}"
        logger.error(msg)
        raise SplTaFwkWaitForDependenciesTimeout(msg)

    def wait_for_test_bootstrap(self, test):
        while True:
            done, pending = self.tasks.bootstrap_tasks_by_state(test.key)
            self._check_failed_tasks(test, done)

            if not pending:
                break
            elif time.time() > self._execution_timeout:
                self._report_timeout(test, pending)

            logger.debug(f"{test} is waiting for dependencies")
            time.sleep(TasksWait.CHECK_FREQUENCY.value)

        logger.debug(f"{test} dependencies are ready")

    def execute_test_inplace_forges(self, test):
        logger.debug(f"Executing inplace forges for test {test}")
        exec_steps = []
        inplace_tasks = self.tasks.get_inplace_tasks(test.key)
        dump = (
            f"Execution matrix for inplace tasks for {test}: {inplace_tasks}"
        )
        for tasks in inplace_tasks:
            dump += f"\t{[tasks]}"
            exec_steps.append([tasks])
        logger.debug(dump)
        self.inplace_tasks_execution(exec_steps)

    def test_error_report(self, test):
        for _, _, task in self.tasks.enumerate_tasks(test.key):
            if task.failed:
                yield task, task.error


dependency_manager = TestDependencyManager()
