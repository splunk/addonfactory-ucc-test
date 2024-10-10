import time
from splunk_add_on_ucc_modinput_test.functional import logger
from splunk_add_on_ucc_modinput_test.functional.exceptions import ( SplTaFwkDependencyExecutionError, SplTaFwkWaitForDependenciesTimeout )
from splunk_add_on_ucc_modinput_test.functional.constants import ForgeScope, TasksWait
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

    def bind(self, test_fn, scope, frg_fns):
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
                logger.debug(f"BIND created frg {id(frg)} - {frg} - {frg.key}")
            else:
                frg = found
                logger.debug(f"BIND found frg {id(frg)} - {frg} - {frg.key}")
            
            frg_list.append(FrameworkTask(test, frg, frg_kwargs, frg_probe))
            
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

    def expand_parametrized_tests(self, parametrized_tests):
        for test_key, param_tests in parametrized_tests.items():
            test = self.unregister_test(test_key)
            if not test:
                logger.debug(f"TEST NOT FOUND: {test.key}")
                continue
                            
            logger.debug(f"Test found: {test.key}")
            test_tasks = self.tasks.remove_test_tasks(test_key)
            assert(test_tasks)
            for test_name, parametrized_kwargs in param_tests:
                logger.debug(
                    f"adding test: {test.key} => test_name: {test_name}, kwargs: {parametrized_kwargs}"
                )
                parametrized_test = FrameworkTest(
                    test._function, test_name
                )
                logger.debug(
                    f"create parametrized test: {parametrized_test.key}, {vars(parametrized_test)}"
                )
                self.tests.add(parametrized_test)

                for parallel_tasks in test_tasks[::-1]:
                    frg_list = []
                    for task in parallel_tasks:
                        frg = task._forge
                        frg.link_test(test.key)
                        parametrized_test.link_forge(frg.key)
                        
                        frg_probe = task.get_probe_fn()
                        frg_kwargs = task.get_forge_kwargs().copy()
                        frg_kwargs.update(parametrized_kwargs)
                        frg_list.append(FrameworkTask(parametrized_test, frg, frg_kwargs, frg_probe))
                    
                    self.tasks.add(frg_list)
                    
                    logger.debug(
                        f"parametrized_test.link_forge: {parametrized_test.key}: {frg_list} => {parametrized_test}"
                    )

    def log_dep_exec_matrix(self, tests, dep_mtx):
        matrix = "\nDependency execution matrix:\n"
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

    def build_dep_exec_matrix(self, skip_tests):
        skipped_test_keys = [test.key for test, _ in skip_tests]
        tests = [
            test
            for test in self.tests.values()
            if test.key not in skipped_test_keys
        ]

        res = []
        step_index = 0
        while True:
            step_tasks = [None] * len(tests)
            for pos, test in enumerate(tests):
                tasks = self.tasks.get_by_test(test.key)
                if step_index < len(tasks):
                    step_tasks[pos] = tasks[step_index]
            if not any(step_tasks):
                break
            res.append(step_tasks)
            step_index += 1

        self.log_dep_exec_matrix(tests, res)
        return res

    def start_dependency_execution(
        self, deps_exec_mtx, sequential_execution, number_of_threads
    ):
        if not deps_exec_mtx:
            return

        if self.executor is None:
            if sequential_execution:
                self.executor = FrmwkSequentialExecutor(self)
            else:
                self.executor = FrmwkParallelExecutor(self, number_of_threads)
            self.executor.start(deps_exec_mtx)
            self._execution_timeout = time.time() + TasksWait.TIMEOUT.value

    def teardown_test_dependencies(self, test):
        tasks = list(self.tasks.enumerate_tasks(test.key))        
        for _, _, task in reversed(tasks):
            task.teardown()

    def teardown_test(self, test):
        logger.debug(f"teardown test:{test}")
        test.mark_executed()
        self.teardown_test_dependencies(test)


    def wait_for_test_dependencies(self, test):
        while True:
            done, pending = self.tasks.tasks_by_state(test.key)
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


    def test_error_report(self, test):
        for _, _, task in self.tasks.enumerate_tasks(test.key):
            if task.failed:
                yield task.error

dependency_manager = TestDependencyManager()
