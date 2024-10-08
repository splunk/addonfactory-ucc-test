import time
from typing import List, Tuple
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
from splunk_add_on_ucc_modinput_test.functional.splunk.client import (
    SplunkClientBase,
)
from splunk_add_on_ucc_modinput_test.functional.vendor.client import (
    VendorClientBase,
)


class TestDependencyManager:
    def __init__(self):
        self.tests = TestCollection()
        self.forges = ForgeCollection()
        self.tasks = TaskCollection()
        self.executor = None
        self._vendor_client_class = VendorClientBase
        self._splunk_client_class = SplunkClientBase

    def set_vendor_client_class(self, cls):
        assert issubclass(cls, VendorClientBase)
        self._vendor_client_class = cls

    def create_vendor_client(self):
        return self._vendor_client_class()

    def set_splunk_client_class(self, cls):
        assert issubclass(cls, SplunkClientBase)
        self._splunk_client_class = cls

    def create_splunk_client(self):
        return self._splunk_client_class()

    def _interpret_forge_data(self, frg_data):
        if isinstance(frg_data, (tuple, list)):
            frg_fn, probe_fn, scope, kwargs = None, None, None, None
            assert len(frg_data) > 1
            frg_fn = frg_data[0]
            if len(frg_data) > 1:
                probe_fn = frg_data[1]
            if len(frg_data) > 2:
                scope = frg_data[2]
            if len(frg_data) > 3:
                kwargs = frg_data[3]
            return frg_fn, probe_fn, scope, kwargs

        return frg_data, None, None, {}

    def _interpret_scope(self, scope, test):
        frg_scope = scope
        if frg_scope is ForgeScope.FUNCTION:
            frg_scope = "::".join(test.key)
        elif frg_scope is ForgeScope.MODULE:
            frg_scope = test.source_file
        return frg_scope

    def bind(self, test_fn, scope, frg_fns, is_bootstrap):
        logger.debug(f"bind: {test_fn} -> {frg_fns}")

        test = self.tests.lookup_by_function(test_fn)
        if not test:
            test = FrameworkTest(test_fn)
            self.tests.add(test)

        frg_group_scope = self._interpret_scope(scope, test)

        frg_list = []
        for frg_data in frg_fns:
            (
                frg_fn,
                frg_probe,
                frg_scope,
                frg_kwargs,
            ) = self._interpret_forge_data(frg_data)
            if frg_scope:
                frg_scope = self._interpret_scope(frg_scope, test)
            else:
                frg_scope = frg_group_scope

            frg = FrameworkForge(frg_fn, frg_scope)
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
                FrameworkTask(test, frg, is_bootstrap, frg_kwargs, frg_probe)
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
        kwargs = src_task.get_forge_kwargs().copy()
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
                        matrix += f"\t\tDependency {'::'.join(task.forge_key[:2])}, scope {task.forge_key[2]}\n"
                else:
                    matrix += "\t\tNo depemdemcies at this step\n"
        logger.info(matrix)

    def build_bootstrap_matrix(self, skip_tests):
        skipped_test_keys = [test.key for test, _ in skip_tests]
        tests = [
            test
            for test in self.tests.values()
            if test.key not in skipped_test_keys
        ]

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

    def start_bootstrap_execution(
        self, deps_exec_mtx, sequential_execution, number_of_threads
    ):
        if self.executor is None:
            if sequential_execution:
                self.executor = FrmwkSequentialExecutor(self)
            else:
                self.executor = FrmwkParallelExecutor(self, number_of_threads)

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

    def wait_for_test_bootstrap(self, test):
        while True:
            done, pending = self.tasks.bootstrap_tasks_by_state(test.key)
            for task in done:
                if task.failed:
                    forge_path = "::".join(task.forge_key[:2])
                    test_path = "::".join(test.key)
                    msg = f"Dependency {forge_path} failed to execute for test {test_path} with error:\n{task.error}"
                    logger.error(msg)
                    raise SplTaFwkDependencyExecutionError(msg)

            if not pending:
                break

            if time.time() > self._execution_timeout:
                msg = f"{test} exceeded {TasksWait.TIMEOUT.value} seconds timeout while waiting for dependencies:"
                for task in pending:
                    forge_path = "::".join(task.forge_key[:2])
                    msg += f"\n\t{forge_path}, self id: {id(task)}, scope: {task.forge_key[2]}, exec_id: {task._exec_id} is_executed: {task.is_executed}, is_failed: {task.failed}"
                logger.error(msg)
                raise SplTaFwkWaitForDependenciesTimeout(msg)

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
                yield task.error


dependency_manager = TestDependencyManager()
