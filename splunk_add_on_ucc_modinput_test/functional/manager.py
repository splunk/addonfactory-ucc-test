# from __future__ import annotations
# from typing import TYPE_CHECKING

# if TYPE_CHECKING:
from splunk_add_on_ucc_modinput_test.typing import (
    ArtifactsType,
    ExecutableKeyType,
)
import time

from typing import (
    Any,
    Callable,
    Dict,
    Generator,
    List,
    Tuple,
    Optional,
    Type,
    Union,
)
from splunk_add_on_ucc_modinput_test.functional import logger
from splunk_add_on_ucc_modinput_test.functional.exceptions import (
    SplTaFwkDependencyExecutionError,
    SplTaFwkWaitForDependenciesTimeout,
)
from splunk_add_on_ucc_modinput_test.functional.constants import (
    ForgeScope,
    BuiltInArg,
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
from splunk_add_on_ucc_modinput_test.functional.vendor import (
    VendorClientBase,
    VendorConfigurationBase,
)

from splunk_add_on_ucc_modinput_test.functional.common.pytest_config_adapter import (
    PytestConfigAdapter,
)
from splunk_add_on_ucc_modinput_test.functional.common.identifier_factory import (
    create_identifier,
    IdentifierType,
)


class forge:
    def __init__(
        self,
        forge_fn: Callable[..., Any],
        *,
        probe: Optional[Callable[..., Any]] = None,
        scope: Optional[Union[ForgeScope, str]] = None,
        **kwargs: ArtifactsType,
    ) -> None:
        self.forge_fn = forge_fn
        self.probe = probe
        self.scope = scope.value if isinstance(scope, ForgeScope) else scope
        self.kwargs = kwargs


class forges:
    def __init__(
        self,
        *forge_list: forge,
        scope: Optional[Union[ForgeScope, str]] = None,
    ) -> None:
        self.forge_list = forge_list
        self.scope = scope.value if isinstance(scope, ForgeScope) else scope


class TestDependencyManager(PytestConfigAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.tests = TestCollection()
        self.forges = ForgeCollection()
        self.tasks = TaskCollection()
        self.executor: None | (
            FrmwkSequentialExecutor | FrmwkParallelExecutor
        ) = None
        self._vendor_clients = {
            BuiltInArg.VENDOR_CLIENT.value: (
                VendorClientBase,
                VendorConfigurationBase,
            )
        }
        self._splunk_clients = {
            BuiltInArg.SPLUNK_CLIENT.value: (
                SplunkClientBase,
                SplunkConfigurationBase,
            )
        }
        self._pytest_config = None
        self._session_id = self.generate_session_id()
        self._global_builtin_args_pool: dict[
            ExecutableKeyType, ArtifactsType
        ] = {}

    @staticmethod
    def generate_session_id() -> str:
        return create_identifier(
            id_type=IdentifierType.ALPHA, in_uppercase=True
        )

    def set_vendor_client_class(
        self,
        vendor_configuration_class: type[VendorConfigurationBase],
        vendor_client_class: type[VendorClientBase],
        vendor_class_argument_name: str,
    ) -> None:
        logger.debug(
            f"set_vendor_client_class: {vendor_client_class}, {vendor_configuration_class}, {vendor_class_argument_name}"
        )
        assert issubclass(vendor_client_class, VendorClientBase)
        assert issubclass(vendor_configuration_class, VendorConfigurationBase)
        self._vendor_clients[vendor_class_argument_name] = (
            vendor_client_class,
            vendor_configuration_class,
        )

    def set_splunk_client_class(
        self,
        splunk_configuration_class: type[SplunkConfigurationBase],
        splunk_client_class: type[SplunkClientBase],
        splunk_class_argument_name: str,
    ) -> None:
        logger.debug(
            f"set_splunk_client_class: {splunk_configuration_class}, {splunk_client_class}, {splunk_class_argument_name}"
        )
        assert issubclass(splunk_client_class, SplunkClientBase)
        assert issubclass(splunk_configuration_class, SplunkConfigurationBase)
        self._splunk_clients[splunk_class_argument_name] = (
            splunk_client_class,
            splunk_configuration_class,
        )

    def create_global_builtin_args(
        self,
    ) -> Dict[str, Union[str, VendorClientBase, SplunkClientBase]]:
        global_builtin_args: Dict[
            str, Union[str, VendorClientBase, SplunkClientBase]
        ] = {
            BuiltInArg.SESSION_ID.value: self.session_id,
        }

        for v_prop, (v_client, v_config) in self._vendor_clients.items():
            v_conf_instance = v_config(self._pytest_config)
            global_builtin_args[v_prop] = v_client(v_conf_instance)
            logger.debug(
                f"create_global_builtin_args, vendor: {v_prop}, v_config={v_conf_instance} config_id={id(v_conf_instance)}, v_client: {global_builtin_args[v_prop]}"
            )

        for s_prop, (s_client, s_config) in self._splunk_clients.items():
            conf_instance = s_config(self._pytest_config)
            global_builtin_args[s_prop] = s_client(conf_instance)
            logger.debug(
                f"create_global_builtin_args, splunk: {s_prop}, s_config={conf_instance} config_id={id(conf_instance)}, s_client: {global_builtin_args[s_prop]}"
            )

        return global_builtin_args

    def get_global_builtin_args(
        self, test_key: ExecutableKeyType
    ) -> dict[str, Any]:
        if test_key not in self._global_builtin_args_pool:
            logger.debug(f"create_global_builtin_args for test {test_key}:")
            self._global_builtin_args_pool[
                test_key
            ] = self.create_global_builtin_args()

        return self._global_builtin_args_pool[test_key]

    @property
    def session_id(self) -> str:
        return self._session_id

    def _interpret_scope(
        self, scope: Optional[str], test: FrameworkTest
    ) -> Optional[str]:
        if scope is None:
            return None

        if scope == ForgeScope.FUNCTION.value:
            scope = test.full_path
        elif scope == ForgeScope.MODULE.value:
            scope = test.source_file

        return scope

    def forge_find_or_make(
        self, forge_fn: Callable[..., Any], scope: str, is_bootstrap: bool
    ) -> FrameworkForge:
        frg = FrameworkForge(forge_fn, scope)
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
        return frg

    def bind(
        self,
        test_fn: Callable[..., Any],
        scope: Optional[str],
        frg_fns: list[forge],
        is_bootstrap: bool,
    ) -> FrameworkTest:
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

            frg = self.forge_find_or_make(f.forge_fn, frg_scope, is_bootstrap)

            frg_list.append(
                FrameworkTask(test, frg, is_bootstrap, f.kwargs, f.probe, self)
            )

            frg.link_test(test.key)
            test.link_forge(frg.key)

        self.tasks.add(frg_list)

        return test

    def unregister_test(self, test_key: FrameworkTest) -> FrameworkTest:
        test = self.tests.pop(test_key, None)
        if test:
            for frg_key in test.forges:
                frg = self.forges.get(frg_key)
                if frg:
                    frg.unlink_test(test.key)
            logger.debug(
                f"unregister_test: Test {test_key} has been unregistered"
            )

        return test

    def find_test(self, test_fn, parametrized_name):
        test_obj = FrameworkTest(test_fn, parametrized_name)
        return self.tests.get(test_obj.key)

    def dump_tests(self) -> None:
        logger.debug(f"DUMP TESTS: {len(self.tests.items())}")
        for key, test in self.tests.items():
            logger.debug(f"test key:{key} value: {test}")

    def copy_task_for_parametrized_test(
        self, test, extra_kwargs, src_task, is_function_scope
    ):
        if is_function_scope:
            frg = self.forge_find_or_make(
                forge_fn=src_task._forge._function,
                scope=test.full_path,
                is_bootstrap=src_task.is_bootstrap,
            )
        else:
            frg = src_task._forge

        frg.link_test(test.key)
        test.link_forge(frg.key)
        probe = src_task.get_probe_fn()
        is_bootstrap = src_task.is_bootstrap
        kwargs = src_task.get_forge_kwargs_copy()
        kwargs.update(extra_kwargs)
        return FrameworkTask(test, frg, is_bootstrap, kwargs, probe, self)

    def expand_parametrized_tests(
        self, parametrized_tests: dict[str, list[tuple[str, Any]]]
    ) -> None:
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

                for parallel_tasks in test_tasks:
                    frg_list = []
                    for src_task in parallel_tasks:
                        is_function_scope = (
                            src_task._forge.scope == test.full_path
                        )
                        parametrized_task = (
                            self.copy_task_for_parametrized_test(
                                parametrized_test,
                                parametrized_kwargs,
                                src_task,
                                is_function_scope,
                            )
                        )
                        frg_list.append(parametrized_task)

                    self.tasks.add(frg_list)

                    logger.debug(
                        f"parametrized_test.link_forge: {parametrized_test.key}: {frg_list} => {parametrized_test}"
                    )

    def _log_dep_exec_matrix(self, tests, dep_mtx) -> None:
        matrix = "\nBootstrap Dependency execution matrix:\n"
        for step_index, group in enumerate(dep_mtx):
            matrix += f"Step {step_index+1}:\n"
            for test_index, test_tasks in enumerate(group):
                matrix += f"\ttest {test_index+1}: {'::'.join(tests[test_index].key)}\n"
                if test_tasks is not None:
                    for task in test_tasks:
                        matrix += f"\t\tDependency {task.forge_full_path}, scope {task.forge_scope}\n"
                else:
                    matrix += "\t\tNo depemdemcies at this step\n"
        logger.info(matrix)

    def remove_skipped_tests(
        self, skipped_tests_keys: list[tuple[str, ...]]
    ) -> None:
        for test_key in skipped_tests_keys:
            self.unregister_test(test_key)

    def synch_tests_with_pytest_list(self, pytest_test_set_keys) -> None:
        tests_to_remove = [
            test_key
            for test_key in self.tests.keys()
            if test_key not in pytest_test_set_keys
        ]
        self.remove_skipped_tests(tests_to_remove)

    def build_bootstrap_matrix(self) -> list[FrameworkTask]:
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

    def start_bootstrap_execution(self) -> None:
        if self.tests.is_empty or self.tasks.is_empty:
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
            self._execution_timeout = time.time() + self.bootstrap_wait_timeout
            self.executor.start(deps_exec_mtx)

    def inplace_tasks_execution(self, deps_exec_mtx):
        logger.debug(f"start inplace_tasks_execution:{deps_exec_mtx}")
        if not deps_exec_mtx:
            return
        assert self.executor is not None
        logger.debug("inplace_tasks_execution is about to start")
        self._execution_timeout = (
            time.time() + self.attached_tasks_wait_timeout
        )
        self.executor.start(deps_exec_mtx)
        self.executor.wait(is_bootstrap=False)

    def shutdown(self) -> None:
        logger.info("Shutting down dependency manager...")

        if self.executor is not None:
            self.executor.shutdown()

    def check_all_tests_executed(self) -> bool:
        executed = [test.is_executed for test in self.tests.values()]
        return all(executed)

    def check_tests_executed(self, tests_keys: list[tuple[str, str]]) -> bool:
        executed = [
            self.tests.get(test_key).is_executed for test_key in tests_keys
        ]
        return all(executed)

    def try_to_unblock_inplace_teardowns(self, test: FrameworkTest) -> None:
        inplace_tasks = self.tasks.enumerate_inplace_tasks(test.key)
        for _, _, task in inplace_tasks:
            if self.check_tests_executed(task.forge_test_keys):
                task.unblock_forge_teardown()

    def teardown_test_dependencies(self, test: FrameworkTest) -> None:
        self.try_to_unblock_inplace_teardowns(test)
        tasks = list(self.tasks.enumerate_tasks(test.key))
        for _, _, task in reversed(tasks):
            task.teardown()

    def teardown_test(self, test: FrameworkTest) -> None:
        logger.debug(f"teardown test:{test}")
        test.mark_executed()
        self.teardown_test_dependencies(test)

    def _check_failed_tasks(self, test: FrameworkTest, done_tasks) -> None:
        failed_tasks = [
            task.forge_key for task in done_tasks if task._setup_errors
        ]
        logger.debug(
            f"DONE TASKS for {test.key}: {[task.forge_key for task in done_tasks]}"
        )
        logger.debug(f"FAILED TASKS for {test.key}: {failed_tasks}")
        for task in done_tasks:
            if task.setup_failed:
                test_path = test.full_path
                msg = f"Dependency {task.forge_full_path} failed to execute for test {test_path} with error:\n{task.setup_error}"
                logger.error(msg)
                raise SplTaFwkDependencyExecutionError(msg)

    def _report_timeout(self, test: FrameworkTest, pending_tasks) -> None:
        msg = f"{test} exceeded {self.bootstrap_wait_timeout} seconds timeout while waiting for dependencies:"
        for task in pending_tasks:
            msg += f"\n\t{task.forge_full_path}, self id: {id(task)}, scope: {task.forge_scope}, exec_id: {task._exec_id} is_executed: {task.is_executed}, is_failed: {task.setup_failed}"
        logger.error(msg)
        raise SplTaFwkWaitForDependenciesTimeout(msg)

    def wait_for_test_bootstrap(self, test: FrameworkTest) -> None:
        while True:
            done, pending = self.tasks.bootstrap_tasks_by_state(test.key)
            self._check_failed_tasks(test, done)

            if not pending:
                break
            elif time.time() > self._execution_timeout:
                self._report_timeout(test, pending)

            logger.debug(f"{test} is waiting for bootstrap dependencies")
            time.sleep(self.completion_check_frequency)

        logger.debug(f"{test} bootstrap dependencies are ready")

    def execute_test_inplace_forges(self, test: FrameworkTest) -> None:
        logger.debug(f"Executing attached forges for test {test}")
        exec_steps = []
        inplace_tasks = self.tasks.get_inplace_tasks(test.key)
        dump = (
            f"Execution matrix for attached forges for {test}: {inplace_tasks}"
        )
        for tasks in inplace_tasks:
            dump += f"\t{[tasks]}"
            exec_steps.append([tasks])
        logger.debug(dump)
        self.inplace_tasks_execution(exec_steps)

    def test_setup_error_report(
        self, test: FrameworkTest
    ) -> Generator[tuple[FrameworkTask, str], None, None]:
        for _, _, task in self.tasks.enumerate_tasks(test.key):
            if task.setup_failed:
                yield task, task.setup_error

    def test_teardown_error_report(
        self, test: FrameworkTest
    ) -> Generator[tuple[FrameworkTask, str], None, None]:
        for _, _, task in self.tasks.enumerate_tasks(test.key):
            if task.teardown_failed:
                yield task, task.teardown_error

    def test_error_report(
        self, test: FrameworkTest
    ) -> Generator[tuple[FrameworkTask, str], None, None]:
        for _, _, task in self.tasks.enumerate_tasks(test.key):
            if task.failed:
                yield task, task.error


dependency_manager = TestDependencyManager()
