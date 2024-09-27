import time
from splunk_add_on_ucc_modinput_test.functional import logger
from splunk_add_on_ucc_modinput_test.functional.constants import ForgeScope
from splunk_add_on_ucc_modinput_test.functional.entities import (
    TestCollection,
    DependencyCollection,
    FrameworkTest,
    FrameworkForge,
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
        self.dependencies = DependencyCollection()
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

    def _interpret_dep_data(self, dep_data):
        if isinstance(dep_data, (tuple, list)):
            dep_fn, probe_fn, scope, kwargs = None, None, None, None
            assert len(dep_data) > 1
            dep_fn = dep_data[0]
            if len(dep_data) > 1:
                probe_fn = dep_data[1]
            if len(dep_data) > 2:
                scope = dep_data[2]
            if len(dep_data) > 3:
                kwargs = dep_data[3]
            return dep_fn, probe_fn, scope, kwargs

        return dep_data, None, None

    def _interpret_scope(self, scope, test):
        dep_scope = scope
        if dep_scope is ForgeScope.FUNCTION:
            dep_scope = "::".join(test.key)
        elif dep_scope is ForgeScope.MODULE:
            dep_scope = test.source_file
        return dep_scope

    def bind(self, test_fn, scope, dep_fns):
        logger.debug(f"bind: {test_fn} -> {dep_fns}")

        test = self.tests.lookup_by_function(test_fn)
        if not test:
            test = FrameworkTest(test_fn)
            self.tests.add(test)

        dep_group_scope = self._interpret_scope(scope, test)

        dep_list = []
        for dep_data in dep_fns:
            (
                dep_fn,
                dep_probe,
                dep_scope,
                dep_kwargs,
            ) = self._interpret_dep_data(dep_data)
            if dep_scope:
                dep_scope = self._interpret_scope(dep_scope, test)
            else:
                dep_scope = dep_group_scope

            dep = FrameworkForge(dep_fn, dep_scope)
            found = self.dependencies.get(dep.key)
            if not found:
                self.dependencies.add(dep)
                logger.debug(f"BIND created dep {id(dep)} - {dep} - {dep.key}")
            else:
                dep = found
                logger.debug(f"BIND found dep {id(dep)} - {dep} - {dep.key}")
            dep_list.append((dep, dep_probe, dep_kwargs))
            dep.link_test(test)

        test.link_dependency(dep_list)
        return test

    def unregister_test(self, test_key):
        test = self.tests.pop(test_key, None)
        if test:
            for dep in test.bound_deps:
                dep.unlink_test(test)
        return test

    def find_test(self, test_fn, parametrized_name):
        test_obj = FrameworkTest(test_fn, parametrized_name)
        dependency_manager.dump_tests()
        logger.debug(
            f"find_test {test_obj.key}, {test_obj} ==>> {test_fn}, {parametrized_name} ==>> {test_obj}"
        )
        return self.tests.get(test_obj.key)

    def dump_tests(self):
        logger.debug(f"DUMP TESTS: {len(self.tests.items())}")
        for key, test in self.tests.items():
            logger.debug(f"test key:{key} value: {test}")

    def expand_parametrized_tests(self, parametrized_tests):
        for test_key, param_tests in parametrized_tests.items():
            test = self.unregister_test(test_key)
            if test:
                logger.debug(
                    f"expand_parametrized_tests: test found: {test.key}"
                )
                for test_name, parametrized_kwargs in param_tests:
                    logger.debug(
                        f"expand_parametrized_tests: adding test: {test.key} => test_name: {test_name}, kwargs: {parametrized_kwargs}"
                    )
                    parametrized_test = FrameworkTest(
                        test._function, test_name
                    )
                    logger.debug(
                        f"create parametrized test: {parametrized_test.key}, {vars(parametrized_test)}"
                    )
                    self.tests.add(parametrized_test)

                    for parallel_tasks in test.dep_tasks[::-1]:
                        dep_list = []
                        for task in parallel_tasks:
                            dep = task._dep
                            dep.link_test(test)
                            dep_probe = task.get_probe_fn()
                            dep_kwargs = task.get_dep_kwargs()
                            dep_list.append((dep, dep_probe, dep_kwargs))
                        parametrized_test.link_dependency(
                            dep_list, parametrized_kwargs
                        )
                        logger.debug(
                            f"parametrized_test.link_dependency: {parametrized_test.key}: {dep_list} => {parametrized_test}"
                        )
            else:
                logger.debug(
                    f"expand_parametrized_tests: TEST NOT FOUND: {test.key}"
                )

    def log_dep_exec_matrix(self, tests, dep_mtx):
        matrix = "\nDependency execution matrix:\n"
        for step_index, group in enumerate(dep_mtx):
            matrix += f"Step {step_index}:\n"
            for test_index, test_tasks in enumerate(group):
                matrix += f"\ttest: {'::'.join(tests[test_index].key)}\n"
                if test_tasks is not None:
                    for task in test_tasks:
                        matrix += f"\t\tDependency {'::'.join(task.dep_key[:2])}, scope {task.dep_key[2]}\n"
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
                if step_index < len(test.dep_tasks):
                    step_tasks[pos] = test.dep_tasks[step_index]
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

    def teardown_test_dependencies(self, test):
        for _, _, dep_task in test.flat_dep_tasks():
            dep_task.teardown()

    def teardown_test(self, test):
        logger.debug(f"teardown test:{test}")
        test.mark_executed()
        self.teardown_test_dependencies(test)

    def wait_for_dependencies(self, test_fn):
        test = self.tests.lookup_by_function(test_fn)
        if test:
            test.wait_for_dependencies()


dependency_manager = TestDependencyManager()
