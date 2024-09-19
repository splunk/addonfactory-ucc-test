import inspect
import time
import types
import uuid
from splunk_add_on_ucc_modinput_test.functional import logger
from splunk_add_on_ucc_modinput_test.functional.constants import BuiltInArg, ForgeProbe
from splunk_add_on_ucc_modinput_test.functional.exceptions import SplTaFwkWaitForProbeTimeout

class FrameworkTask:
    def __init__(self, test, dependency, dep_kwargs={}, probe_fn=None):
        self._test = test
        self._dep = dependency
        self._dep_kwargs = dep_kwargs
        self._exec_id = None
        self._is_executed = False
        self._teardown = None
        self._error = None
        self._result = None
        self._splunk_client = None
        self._vendor_client = None
        self.apply_probe(probe_fn)

    def __repr__(self):
        return f"{id(self)} - {super().__repr__()}, is_executed={self.is_executed} , dep: {id(self._dep)} - {self._dep} - {self.dep_key}"

    @property
    def is_executed(self):
        return self._is_executed

    @property
    def error(self):
        return self._error

    @property
    def result(self):
        return self._result

    @property
    def has_probe(self):
        return callable(self._probe_gen)

    @property
    def has_teardown(self):
        is_callable = callable(self._teardown)
        is_generator = inspect.isgenerator(self._teardown)
        logger.debug(
            f"HAS TEARDOWN:\n\tTASK: {self.test_key}\n\tFORGE: {self.dep_key}\n\tteardown: {self._teardown}\n\tcallable: {is_callable}\n\tisgenerator: {is_generator}"
        )
        return is_callable or is_generator

    @property
    def ready_to_teardown(self):
        return self.has_teardown and self._dep.all_tests_executed

    @property
    def dep_key(self):
        return self._dep.key

    @property
    def test_key(self):
        return self._test.key

    @property
    def default_artifact_name(self):
        return self._dep.original_name

    def make_result(self, test_result):
        if test_result is None:
            return {}
        if not isinstance(test_result, dict):
            return {self.default_artifact_name: test_result}
        return test_result

    def apply_probe(self, probe_fn):
        self._probe_fn = probe_fn
        if inspect.isgeneratorfunction(self._probe_fn):
            self._probe_gen = probe_fn
        elif callable(self._probe_fn):

            def _probe_default_gen(**probe_args):
                while not probe_fn(**probe_args):
                    yield ForgeProbe.DEFAULT_INTERVAL.value

            self._probe_gen = _probe_default_gen
        else:
            self._probe_gen = None

        if self._probe_gen:
            sig = inspect.signature(self._probe_fn)
            self._probe_required_args = list(sig.parameters.keys())
        else:
            self._probe_required_args = []

    def collect_available_kwargs(self):
        available_kwargs = self._dep_kwargs.copy()
        available_kwargs.update(self._test.artifacts)
        available_kwargs[BuiltInArg.SPLUNK_CLIENT.value] = self._splunk_client
        available_kwargs[BuiltInArg.VENDOR_CLIENT.value] = self._vendor_client
        return available_kwargs

    def prepare_forge_call_args(self, splunk_client, vendor_client):
        logger.debug(f"EXECTASK: prepare_forge_call_args {self}")

        self._splunk_client = splunk_client
        self._vendor_client = vendor_client

        available_kwargs = self.collect_available_kwargs()
        self._call_args = self._dep.filter_requied_kwargs(available_kwargs)

        logger.debug(
            f"EXECTASK: prepare_forge_call_args for {self.dep_key}:\n\t_test._required_args: {self._dep._required_args}\n\t_test._required_args: {self._test._required_args}\n\t_dep_kwargs: {self._dep_kwargs}\n\t_test.artifacts: {self._test.artifacts}\n\tavailable_kwargs: {available_kwargs}\n\t_call_args: {self._call_args}"
        )

    def get_comparable_args(self):
        args_without_clients = self._call_args.copy()
        args_without_clients.pop(BuiltInArg.SPLUNK_CLIENT.value, None)
        args_without_clients.pop(BuiltInArg.VENDOR_CLIENT.value, None)
        return args_without_clients

    def get_dep_kwargs(self):
        return self._dep_kwargs

    def get_probe_fn(self):
        return self._probe_fn

    def get_probe_args(self):
        available_kwargs = self.collect_available_kwargs()

        return {
            k: v for k, v in available_kwargs.items() if k in self._probe_required_args
        }

    def wait_for_probe(self, last_result):
        logger.debug(f"WAIT FOR PROBE started\n\ttest {self.test_key}\n\tforge {self.dep_key}\n\tprobe {self._probe_fn}")
        if not self._probe_gen:
            return

        probe_args = self.get_probe_args()
        probe_args.update(self.make_result(last_result))
        expire_time = time.time() + ForgeProbe.MAX_WAIT_TIME.value
        logger.debug(f"WAIT FOR PROBE\n\ttest {self.test_key}\n\tforge {self.dep_key}\n\tprobe {self._probe_fn}\n\tprobe_gen {self._probe_gen}\n\tprobe_args {probe_args}")
        for interval in self._probe_gen(**probe_args):
            if time.time() > expire_time:
                msg = f"Test {self.test_key}, forge {self.dep_key}: probe {self._probe_fn} exceeted {ForgeProbe.MAX_WAIT_TIME.value} seconds timeout"
                raise SplTaFwkWaitForProbeTimeout(msg)

            if interval > ForgeProbe.MAX_INTERWAL.value:
                interval = ForgeProbe.MAX_INTERWAL.value
            elif interval < ForgeProbe.MIN_INTERVAL.value:
                interval = ForgeProbe.MIN_INTERVAL.value
            time.sleep(interval)

    def completed_with_error(self, error):
        self._error = error
        self._is_executed = True

    def _save_generator_teardown(self, gen):
        self._teardown = gen

    def _save_class_teardown(self):
        if not isinstance(self._dep._function, types.FunctionType):
            attr = getattr(self._dep._function, "teardown", None)
            if callable(attr):
                self._teardown = attr

    def update_test_artifacts(self, artifacts):
        self._test.update_artifacts(artifacts)

    @staticmethod
    def same_args(args1, args2):
        if type(args1) != type(args2):
            return False

        if isinstance(args1, (list, tuple)):
            if len(args1) != len(args2):
                return False
            for arg1, arg2 in zip(args1, args2):
                if not FrameworkTask.same_args(arg1, arg2):
                    return False
            return True

        if isinstance(args1, dict):
            if len(args1) != len(args2):
                return False
            if set(args1.keys()).difference(set(args1.keys())):
                return False
            if set(args2.keys()).difference(set(args1.keys())):
                return False
            for k, v in args1.items():
                if not FrameworkTask.same_args(v, args2[k]):
                    return False
            return True

        return args1 == args2

    def same_tasks(self, other_task):
        if self.dep_key != other_task.dep_key:
            return False

        args1 = self.get_comparable_args()
        args2 = other_task.get_comparable_args()
        return FrameworkTask.same_args(args1, args2)

    def reuse_execution(self, exec_id, result):
        logger.debug(
            f"reuse execution {exec_id}:\n\tTask: {self.test_key}\n\tDep: {self.dep_key}\n\result: {result}"
        )
        self._dep.reuse_execution(exec_id)
        self._exec_id = exec_id
        self._result = result
        self._is_executed = True

    def use_previous_executions(self, args):
        logger.debug(
            f"Dep {self.dep_key}: look for {self._call_args} in {self._dep.executions}"
        )
        for prev_exec in self._dep.executions:
            logger.debug(
                f"EXECTASK: COMPARE ARGS:\n\tprev exec: {prev_exec.kwargs}\n\tcurrent args {args}"
            )
            if self.same_args(prev_exec.kwargs, args):
                logger.info(
                    f"EXECTASK: skip execution {self}, take previous res: {prev_exec.result}, {type(prev_exec.result)}"
                )
                self.reuse_execution(prev_exec.id, prev_exec.result)
                return True
        return False

    def execute(self):
        logger.debug(
            f"EXECTASK: execute {self} - executions {self._dep.executions}, dep_kwargs: {self._call_args}"
        )
        comp_kwargs = self.get_comparable_args()
        if not self.use_previous_executions(comp_kwargs):
            self._exec_id = str(uuid.uuid4())
            logger.debug(
                f"\nEXECTASK: execute {self} - similar executions not found,\n\tTEST: {self.test_key},\n\tself._required_args: {self._dep._required_args},\n\tself._dep_kwargs: {self._dep_kwargs},\n\tcall_args: {self._call_args},\n\ttest artifacts: {self._test.artifacts}"
            )
            if self._dep._is_generatorfunction:
                logger.debug(
                    f"EXECTASK: dependency {self._dep} is a generator function"
                )
                it = self._dep._function(**self._call_args)
                try:
                    result = next(it)
                    self._save_generator_teardown(it)
                except StopIteration as sie:
                    result = sie.value
            else:
                result = self._dep._function(**self._call_args)
                self._save_class_teardown()

            self._result = result
            self._dep.register_execution(
                self._exec_id, self._teardown, comp_kwargs, result
            )
            logger.debug(
                f"EXECTASK: execute {self._dep}, execution res: {result}, {type(result)}"
            )
            self.wait_for_probe(result)
            self._is_executed = True

        logger.debug(
            f"EXECTASK: mark_executed {id(self)} - {self}, dep: {id(self._dep)} - {self._dep} - {self.dep_key}"
        )

    def teardown(self):
        logger.debug(f"EXECTASK: dep {self} teardown {self._teardown}")
        self._dep.teardown(self._exec_id)
