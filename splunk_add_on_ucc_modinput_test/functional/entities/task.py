from __future__ import annotations
import inspect
import time
import types
import random
import traceback
from typing import Tuple, Optional
from splunk_add_on_ucc_modinput_test.functional import logger
from splunk_add_on_ucc_modinput_test.functional.constants import (
    BuiltInArg,
    ForgeProbe,
)
from splunk_add_on_ucc_modinput_test.functional.exceptions import (
    SplTaFwkWaitForProbeTimeout,
)

class FrameworkTask:
    def __init__(self, test, forge, is_bootstrap, forge_kwargs, probe_fn):
        self._test = test
        self._forge = forge
        self._is_bootstrap = is_bootstrap
        self._forge_initial_kwargs = forge_kwargs
        self._probe_kwargs = {}
        self._exec_id = None
        self._is_executed = False
        self._teardown = None
        self._errors = []
        self._result = None
        self._splunk_client = None
        self._vendor_client = None
        self.apply_probe(probe_fn)

    def __repr__(self):
        return f"{id(self)} - {super().__repr__()}, is_executed={self.is_executed} , dep: {id(self._forge)} - {self._forge} - {self.forge_key}"

    @property
    def is_bootstrap(self):
        return self._is_bootstrap

    @property
    def is_executed(self):
        return self._is_executed

    @property
    def error(self):
        return "\n".join(self._errors)

    @property
    def failed(self):
        return bool(self._errors)

    @property
    def result(self):
        return self._result

    @property
    def has_probe(self):
        return callable(self._probe_gen)

    @property
    def forge_key(self):
        return self._forge.key

    @property
    def forge_test_keys(self):
        return list(self._forge.tests)

    @property
    def test_key(self):
        return self._test.key

    @property
    def summary(self):
        test_str = "::".join(self.test_key)
        forge_str = f"{'::'.join(self.forge_key[:2])}, scope: {self.forge_key[2]}, exec_id: {self._exec_id}"
        
        return (
            f"test: {test_str},\n" +
            f"forge: {forge_str},\n" +
            f"forge kwargs: {self._forge_kwargs},\n" +
            f"probe: {self._forge.key},\n" +
            f"probe kwargs: {self._probe_kwargs},\n"
        )

    @property
    def default_artifact_name(self):
        return self._forge.original_name

    def block_forge_teardown(self):
        logger.debug(f"BLOCK teardown for forge {self._forge.key}")
        self._forge.block_teardown()

    def unblock_forge_teardown(self):       
        logger.debug(f"UNBLOCK teardown for forge {self._forge.key}")
        self._forge.unblock_teardown()

    def make_kwarg(self, test_result):
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
        available_kwargs = self._forge_initial_kwargs.copy()
        available_kwargs.update(self._test.artifacts)
        available_kwargs[BuiltInArg.SPLUNK_CLIENT.value] = self._splunk_client
        available_kwargs[BuiltInArg.VENDOR_CLIENT.value] = self._vendor_client
        return available_kwargs

    def prepare_forge_call_args(self, splunk_client, vendor_client):
        logger.debug(f"EXECTASK: prepare_forge_call_args {self}")

        self._splunk_client = splunk_client
        self._vendor_client = vendor_client

        available_kwargs = self.collect_available_kwargs()
        self._forge_kwargs = self._forge.filter_requied_kwargs(available_kwargs)

        logger.debug(
            f"EXECTASK: prepare_forge_call_args for {self.forge_key}:\n\t_test._required_args: {self._forge._required_args}\n\t_test._required_args: {self._test._required_args}\n\t_forge_kwargs: {self._forge_initial_kwargs}\n\t_test.artifacts: {self._test.artifacts}\n\tavailable_kwargs: {available_kwargs}\n\_forge_kwargs: {self._forge_kwargs}"
        )

    def get_comparable_args(self):
        args_without_clients = self._forge_kwargs.copy()
        args_without_clients.pop(BuiltInArg.SPLUNK_CLIENT.value, None)
        args_without_clients.pop(BuiltInArg.VENDOR_CLIENT.value, None)
        return args_without_clients

    def get_forge_kwargs(self):
        return self._forge_initial_kwargs

    def get_probe_fn(self):
        return self._probe_fn

    def invoke_probe(self):
        yield from self._probe_gen(**self._probe_kwargs)

    def prepare_probe_kwargs(self, extra_args={}):
        available_kwargs = self.collect_available_kwargs()
        available_kwargs.update(extra_args)

        self._probe_kwargs = {
            k: v
            for k, v in available_kwargs.items()
            if k in self._probe_required_args
        }

    def wait_for_probe(self, last_result):
        logger.debug(
            f"WAIT FOR PROBE started\n\ttest {self.test_key}\n\tforge {self.forge_key}\n\tprobe {self._probe_fn}"
        )
        if not self._probe_gen:
            return

        extra_args = self.make_kwarg(last_result)
        self.prepare_probe_kwargs(extra_args)
        expire_time = time.time() + ForgeProbe.MAX_WAIT_TIME.value
        logger.debug(
            f"WAIT FOR PROBE\n\ttest {self.test_key}\n\tforge {self.forge_key}\n\tprobe {self._probe_fn}\n\tprobe_gen {self._probe_gen}\n\tprobe_args {self._probe_kwargs}"
        )
        for interval in self.invoke_probe():
            if time.time() > expire_time:
                msg = f"Test {self.test_key}, forge {self.forge_key}: probe {self._probe_fn} exceeded {ForgeProbe.MAX_WAIT_TIME.value} seconds timeout"
                raise SplTaFwkWaitForProbeTimeout(msg)

            if interval > ForgeProbe.MAX_INTERWAL.value:
                interval = ForgeProbe.MAX_INTERWAL.value
            elif interval < ForgeProbe.MIN_INTERVAL.value:
                interval = ForgeProbe.MIN_INTERVAL.value
            time.sleep(interval)

    def mark_as_executed(self):
        self._is_executed = True
        forge_path = "::".join(self.forge_key[:2])
        logger.debug(
            f"MARK TASK EXECUTED: {forge_path}, self id: {id(self)},\n\tscope: {self.forge_key[2]},\n\texec_id: {self._exec_id},\n\tis_executed: {self.is_executed},\n\tis_failed: {self.failed}"
        )
        
    def _save_generator_teardown(self, gen):
        self._teardown = gen

    def _save_class_teardown(self):
        if not isinstance(self._forge._function, types.FunctionType):
            attr = getattr(self._forge._function, "teardown", None)
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
        if self.forge_key != other_task.forge_key:
            return False

        args1 = self.get_comparable_args()
        args2 = other_task.get_comparable_args()
        return FrameworkTask.same_args(args1, args2)

    def reuse_forge_execution(self, exec_id, result, errors):
        logger.debug(
            f"reuse execution {exec_id}:\n\tTask: {self.test_key}\n\tDep: {self.forge_key}\n\result: {result}"
        )
        self._forge.reuse_execution(exec_id)
        self._exec_id = exec_id
        self._result = result
        self.errors = errors

    def use_previous_executions(self, args_to_match) -> Tuple[bool, Optional[object]]:
        logger.debug(
            f"Dep {self.forge_key}: look for {self._forge_kwargs} in {self._forge.executions}"
        )
        for prev_exec in self._forge.executions:
            logger.debug(
                f"EXECTASK: COMPARE ARGS:\n\tprev exec: {prev_exec.kwargs}\n\tcurrent args {args_to_match}"
            )
            if self.same_args(prev_exec.kwargs, args_to_match):
                self.reuse_forge_execution(prev_exec.id, prev_exec.result, prev_exec.errors)
                logger.info(
                    f"EXECTASK self id: {id(self)}: skip execution {self}, take previous res: {prev_exec.result}, {type(prev_exec.result)}"
                )
                return True, prev_exec.result
        return False, None

    def execute(self):
        logger.debug(
            f"EXECTASK: execute {self} - executions {self._forge.executions}, dep_kwargs: {self._forge_kwargs}"
        )
        comp_kwargs = self.get_comparable_args()
        reuse, result = self.use_previous_executions(comp_kwargs)
        if not reuse:
            self._exec_id = f"{int(time.time()*1000000)}{random.randint(0, 1000):03}"
            logger.debug(
                f"\nEXECTASK self id: {id(self)}: execute {self} - similar executions not found,\n\tTEST: {self.test_key},\n\tself._required_args: {self._forge._required_args},\n\tself._forge_initial_kwargs: {self._forge_initial_kwargs},\n\tcall_args: {self._forge_kwargs},\n\ttest artifacts: {self._test.artifacts}"
            )
            try:
                result = None
                if self._forge._is_generatorfunction:
                    logger.debug(
                        f"EXECTASK: dependency {self._forge} is a generator function"
                    )
                    it = self._forge._function(**self._forge_kwargs)
                    try:
                        result = next(it)
                        self._save_generator_teardown(it)
                    except StopIteration as sie:
                        result = sie.value
                else:
                    result = self._forge._function(**self._forge_kwargs)
                    self._save_class_teardown()
            except Exception as e:
                traceback_info = traceback.format_exc()
                report = f"Error in forge: {e}\n{self.summary}\n{traceback_info}"
                logger.error(report)
                self._errors.append(report)

            self._result = result
            self._forge.register_execution(
                self._exec_id, self._teardown, comp_kwargs, result, self._errors
            )
            if not self.is_bootstrap:
                self.block_forge_teardown()

        try:
            if not self.failed:
                self.wait_for_probe(result)
        except Exception as e:
            traceback_info = traceback.format_exc()                
            report = f"Error in probe: {e}\n{self.summary}\n{traceback_info}"
            logger.error(report)
            self._errors.append(report)
        
        self.mark_as_executed()

    def teardown(self):
        logger.debug(f"EXECTASK: dep {self} teardown {self._teardown}")
        try:
            self._forge.teardown(self._exec_id)
        except Exception as e:
            traceback_info = traceback.format_exc()                
            report = f"Error in forge teardown: {e}\n{self.summary}\n{traceback_info}"
            logger.error(report)
            self._errors.append(report)
            
