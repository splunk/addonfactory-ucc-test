#
# Copyright 2025 Splunk Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from __future__ import annotations
from typing import TYPE_CHECKING

from splunk_add_on_ucc_modinput_test.typing import (
    ArtifactsType,
    ForgeGenType,
    ProbeGenType,
)

if TYPE_CHECKING:
    from splunk_add_on_ucc_modinput_test.typing import (
        ProbeFnType,
        ProbeGenFnType,
        ExecutableKeyType,
    )

import inspect
import time
import types
import random
import traceback
from copy import deepcopy
from typing import Any, Generator, Optional, List
from splunk_add_on_ucc_modinput_test.functional import logger
from splunk_add_on_ucc_modinput_test.functional.common.pytest_config_adapter import (
    PytestConfigAdapter,
)
from splunk_add_on_ucc_modinput_test.functional.constants import ForgeProbe

from splunk_add_on_ucc_modinput_test.functional.entities.forge import (
    FrameworkForge,
)
from splunk_add_on_ucc_modinput_test.functional.entities.test import (
    FrameworkTest,
)
from splunk_add_on_ucc_modinput_test.functional.exceptions import (
    SplTaFwkWaitForProbeTimeout,
)
from splunk_add_on_ucc_modinput_test.functional.entities.executable import (
    ExecutableBase,
)
from splunk_add_on_ucc_modinput_test.functional.splunk import SplunkClientBase
from splunk_add_on_ucc_modinput_test.functional.vendor import VendorClientBase


class FrameworkTask:
    def __init__(
        self,
        test: FrameworkTest,
        forge: FrameworkForge,
        is_bootstrap: bool,
        forge_kwargs: dict[str, Any],
        probe_fn: ProbeFnType | None,
        config: PytestConfigAdapter,
    ):
        self._config = config
        self._test = test
        self._forge = forge
        self._is_bootstrap = is_bootstrap
        self._forge_initial_kwargs = forge_kwargs
        self._exec_id: str | None = None
        self._is_executed = False
        self._teardown: Generator[None, None, None] | None = None
        self._setup_errors: list[str] = []
        self._teardown_errors: list[str] = []
        self._result: object | None = None
        self._global_builtin_args: dict[str, Any] = {}
        self._forge_kwargs: dict[str, Any] = {}
        self._probe: ExecutableBase | None = None
        self._probe_fn: ProbeFnType | None = None
        self._probe_gen: ProbeGenFnType | None = None
        self._probe_kwargs: dict[str, Any] = {}
        self.apply_probe(probe_fn)

    def __repr__(self) -> str:
        return f"{id(self)} - {super().__repr__()}, is_executed={self.is_executed}, is_bootstrap={self._is_bootstrap}, dep: {id(self._forge)} - {self._forge} - {self.forge_key}"

    @property
    def is_bootstrap(self) -> bool:
        return self._is_bootstrap

    @property
    def is_executed(self) -> bool:
        return self._is_executed

    @property
    def error(self) -> str:
        errors = self._setup_errors + self._teardown_errors
        return "\n".join(errors)

    @property
    def setup_error(self) -> str:
        return "\n".join(self._setup_errors)

    @property
    def teardown_error(self) -> str:
        return "\n".join(self._teardown_errors)

    @property
    def setup_failed(self) -> bool:
        return bool(self._setup_errors)

    @property
    def teardown_failed(self) -> bool:
        return bool(self._teardown_errors)

    @property
    def failed(self) -> bool:
        return self.setup_failed or self.teardown_failed

    @property
    def result(self) -> object:
        return self._result

    @property
    def forge_key(self) -> tuple[str, ...]:
        return self._forge.key

    @property
    def forge_scope(self) -> str:
        return self._forge.scope

    @property
    def forge_test_keys(self) -> list[ExecutableKeyType]:
        return list(self._forge.tests_keys)

    @property
    def forge_name(self) -> str:
        return self.forge_key[1]

    @property
    def forge_path(self) -> str:
        return self.forge_key[0]

    @property
    def forge_full_path(self) -> str:
        return "::".join(self.forge_key[:2])

    @property
    def test_key(self) -> tuple[str, ...]:
        return self._test.key

    @property
    def test_name(self) -> str:
        return self._test.name

    @property
    def test_path(self) -> str:
        return self._test.path

    @property
    def test_full_path(self) -> str:
        return self._test.full_path

    @property
    def probe_name(self) -> str | None:
        if self._probe:
            return self._probe.key[1]
        return None

    @property
    def probe_path(self) -> str | None:
        if self._probe:
            return self._probe.key[0]
        return None

    @property
    def probe_full_path(self) -> str | None:
        if self._probe:
            return "::".join(self._probe.key)
        return None

    @property
    def summary(self) -> str:
        return (
            f"\ntest: {self.test_name},"
            + f"\n\tlocation: {self.test_path},"
            + f"\n\tforge: {self.forge_name},"
            + f"\n\t\tlocation: {self.forge_path},"
            + f"\n\t\tscope: {self.forge_scope},"
            + f"\n\t\texec id: {self._exec_id},"
            + f"\n\t\tkwargs: {self._forge_kwargs},"
            + f"\n\tprobe: {self.probe_name},"
            + f"\n\t\tlocation: {self.probe_path},"
            + f"\n\t\tkwargs: {self._probe_kwargs},"
        )

    @property
    def default_artifact_name(self) -> str:
        return self._forge.original_name

    def block_forge_teardown(self) -> None:
        logger.debug(f"BLOCK teardown for forge {self._forge.key}")
        self._forge.block_teardown()

    def unblock_forge_teardown(self) -> None:
        logger.debug(f"UNBLOCK teardown for forge {self._forge.key}")
        self._forge.unblock_teardown()

    def make_kwarg(self, test_result: object | None) -> ArtifactsType:
        if test_result is None:
            return {}
        elif not isinstance(test_result, dict):
            return {self.default_artifact_name: test_result}
        else:
            return test_result

    def apply_probe(self, probe_fn: ProbeFnType | None) -> None:
        self._probe_fn = probe_fn
        if callable(probe_fn):
            self._probe = ExecutableBase(probe_fn)

        if inspect.isgeneratorfunction(self._probe_fn):
            self._probe_gen = probe_fn
        elif callable(self._probe_fn):

            def _probe_default_gen(
                **probe_args: Any,
            ) -> Generator[int, None, bool]:
                if probe_fn is not None:
                    while not probe_fn(**probe_args):
                        yield self._config.probe_invoke_interval
                return True

            self._probe_gen = _probe_default_gen
        else:
            self._probe_gen = None

        if self._probe_gen and self._probe_fn is not None:
            sig = inspect.signature(self._probe_fn)
            self._probe_required_args = list(sig.parameters.keys())
        else:
            self._probe_required_args = []

    def collect_available_kwargs(self) -> dict[str, Any]:
        available_kwargs = self._test.artifacts_copy
        available_kwargs.update(self.get_forge_kwargs_copy())
        available_kwargs.update(self._global_builtin_args)
        available_kwargs.update(self._test.builtin_args)
        return available_kwargs

    def prepare_forge_call_args(
        self, global_builtin_args: dict[str, Any]
    ) -> None:
        logger.debug(f"EXECTASK: prepare_forge_call_args {self}")

        self._global_builtin_args = global_builtin_args

        available_kwargs = self.collect_available_kwargs()
        self._forge_kwargs = self._forge.filter_requied_kwargs(
            available_kwargs
        )

        logger.debug(
            f"EXECTASK: prepare_forge_call_args for {self.forge_key}:\n\ttest required args: {self._test.required_args_names}\n\ttest artifacts: {self._test.artifacts}\n\tforge initial kwargs: {self._forge_initial_kwargs}\n\tforge kwargs: {self._forge_kwargs}\n\ttask available kwargs: {available_kwargs}"
        )

    def _get_comparable_args(self) -> dict[str, Any]:
        return {
            k: v
            for k, v in self._forge_kwargs.items()
            if not isinstance(v, (SplunkClientBase, VendorClientBase))
        }

    def get_forge_kwargs_copy(self) -> dict[str, Any]:
        try:
            # make a copy of initial arguments if possible
            return deepcopy(self._forge_initial_kwargs)
        except TypeError:
            # copy is not possible, get initial arguments by reference
            logger.warning(
                f"deepcopy of forge initial arguments is not possible, returning them by reference.{self.summary}"
            )
            return self._forge_initial_kwargs

    def get_probe_fn(self) -> ProbeFnType | None:
        return self._probe_fn

    def invoke_probe(self) -> ProbeGenType:
        if callable(self._probe_gen):
            result = yield from self._probe_gen(**self._probe_kwargs)
            return result
        return None

    def prepare_probe_kwargs(self, extra_args: dict[str, Any] = {}) -> None:
        available_kwargs = self.collect_available_kwargs()
        available_kwargs.update(extra_args)

        self._probe_kwargs = {
            k: v
            for k, v in available_kwargs.items()
            if k in self._probe_required_args
        }

    def wait_for_probe(self, last_result: ArtifactsType) -> bool | None:
        logger.debug(
            f"WAIT FOR PROBE started\n\ttest {self.test_key}\n\tforge {self.forge_key}\n\tprobe {self._probe_fn}"
        )
        if not self._probe_gen:
            return None

        probe_start_time = time.time()
        self.prepare_probe_kwargs(last_result)
        expire_time = time.time() + self._config.probe_wait_timeout
        logger.debug(
            f"WAIT FOR PROBE\n\ttest {self.test_key}\n\tforge {self.forge_key}\n\tprobe {self._probe_fn}\n\tprobe_gen {self._probe_gen}\n\tprobe_args {self._probe_kwargs}"
        )

        result = None
        try:
            it = self.invoke_probe()
            while True:
                interval = next(it)
                if time.time() > expire_time:
                    result = False
                    msg = f"Test {self.test_key}, forge {self.forge_key}: probe {self._probe_fn} exceeded {self._config.probe_wait_timeout} seconds timeout"
                    raise SplTaFwkWaitForProbeTimeout(msg)

                if not isinstance(interval, int):
                    interval = self._config.probe_invoke_interval
                elif interval > ForgeProbe.MAX_INTERVAL.value:
                    interval = ForgeProbe.MAX_INTERVAL.value
                elif interval < ForgeProbe.MIN_INTERVAL.value:
                    interval = ForgeProbe.MIN_INTERVAL.value
                time.sleep(interval)
        except StopIteration as sie:
            result = sie.value

        logger.info(
            f"Forge probe has finished execution, result: {result}, time taken {time.time() - probe_start_time} seconds:{self.summary}"
        )

        return result

    def mark_as_failed(self, error: str | Exception, prefix: str) -> None:
        if isinstance(error, Exception):
            traceback_info = traceback.format_exc()
            report = f"{prefix}: {error}{self.summary}\n{traceback_info}"
        else:
            report = f"{prefix}: {error}{self.summary}"
        logger.error(report)
        self._setup_errors.append(report)
        self._is_executed = True

    def mark_as_executed(self) -> None:
        self._is_executed = True
        logger.debug(
            f"MARK TASK EXECUTED: {self.forge_full_path},\n\tself id: {id(self)},\n\tscope: {self.forge_scope},\n\texec_id: {self._exec_id},\n\ttest: {self.test_key},\n\tis_executed: {self.is_executed},\n\tis_failed: {self.failed},\n\terrors: {self._setup_errors}"
        )

    def _save_generator_teardown(self, gen: ForgeGenType | None) -> None:
        self._teardown = gen

    def _save_class_teardown(self) -> None:
        if not isinstance(self._forge._function, types.FunctionType):
            attr = getattr(self._forge._function, "teardown", None)
            if callable(attr):
                self._teardown = attr

    def update_test_artifacts(self, artifacts: dict[str, Any]) -> None:
        self._test.update_artifacts(artifacts)

    @staticmethod
    def same_args(args1: Any, args2: Any) -> bool:
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

    def same_tasks(self, other_task: FrameworkTask) -> bool:
        if self.forge_key != other_task.forge_key:
            return False

        args1 = self._get_comparable_args()
        args2 = other_task._get_comparable_args()
        return FrameworkTask.same_args(args1, args2)

    def reuse_forge_execution(
        self, exec_id: str, result: Any, errors: list[str]
    ) -> None:
        logger.debug(
            f"reuse execution {exec_id}:\n\tTask: {self.test_key}\n\tDep: {self.forge_key}\n\tresult: {result}\n\terrors: {errors}"
        )
        self._forge.reuse_execution(exec_id)
        self._exec_id = exec_id
        self._result = result
        self._setup_errors = errors

    def use_previous_executions(
        self, args_to_match: ArtifactsType
    ) -> tuple[bool, ArtifactsType]:
        logger.debug(
            f"Dep {self.forge_key}: look for {self._forge_kwargs} in {self._forge.executions}"
        )
        for prev_exec in self._forge.executions:
            logger.debug(
                f"EXECTASK: COMPARE ARGS:\n\tprev exec: {prev_exec.kwargs}\n\tcurrent args {args_to_match}"
            )
            if self.same_args(prev_exec.kwargs, args_to_match):
                self.reuse_forge_execution(
                    prev_exec.id, prev_exec.result, prev_exec.errors
                )
                logger.info(f"Forge execution has been REUSED:{self.summary}")
                return True, prev_exec.result
        return False, {}

    def execute(self) -> None:
        logger.debug(
            f"EXECTASK: execute {self}:\n\texecutions {self._forge.executions}\n\tdep_kwargs: {self._forge_kwargs}\n\tprobe {self._probe_fn}"
        )
        comp_kwargs = self._get_comparable_args()
        reuse, result = self.use_previous_executions(comp_kwargs)
        if not reuse:
            self._exec_id = (
                f"{int(time.time()*1000000)}{random.randint(0, 1000):03}"
            )
            logger.debug(
                f"\nEXECTASK self id: {id(self)}: execute {self} - similar executions not found,\n\tTEST: {self.test_key},\n\tself._required_args: {self._forge._required_args},\n\tself._forge_initial_kwargs: {self._forge_initial_kwargs},\n\tcall_args: {self._forge_kwargs},\n\ttest artifacts: {self._test.artifacts}"
            )
            try:
                forge_start_time = time.time()
                if self._forge._is_generatorfunction:
                    logger.debug(
                        f"EXECTASK: dependency {self._forge} is a generator function"
                    )
                    it = self._forge._function(**self._forge_kwargs)
                    try:
                        result = self.make_kwarg(next(it))
                        self._save_generator_teardown(it)
                    except StopIteration as sie:
                        result = self.make_kwarg(sie.value)
                else:
                    result = self.make_kwarg(
                        self._forge._function(**self._forge_kwargs)
                    )
                    self._save_class_teardown()
                logger.info(
                    f"Forge has been executed successfully, time taken {time.time() - forge_start_time} seconds:{self.summary}"
                )
            except Exception as e:
                traceback_info = traceback.format_exc()
                report = f"Forge has failed to execute: {e}{self.summary}\n{traceback_info}"
                logger.error(report)
                self._setup_errors.append(report)

        try:
            if not self.setup_failed:
                probe_res = self.wait_for_probe(result)
                probe_fn = self.get_probe_fn()
                if probe_res is not None and probe_fn is not None:
                    result[probe_fn.__name__] = probe_res
        except Exception as e:
            traceback_info = traceback.format_exc()
            report = f"Forge probe has failed to execute: {e}{self.summary}\n{traceback_info}"
            logger.error(report)
            self._setup_errors.append(report)

        if not reuse:
            self._result = result
            assert (
                self._exec_id is not None
            ), "_exec_id must be assigned earlier in this method"
            self._forge.register_execution(
                self._exec_id,
                teardown=self._teardown,
                kwargs=comp_kwargs,
                result=self._result,
                errors=self._setup_errors,
            )
            if not self.is_bootstrap:
                self.block_forge_teardown()

        self.mark_as_executed()

    def teardown(self) -> None:
        logger.debug(
            f"Teardown task\n\t_exec_id: {self._exec_id}\n\tforge: {self.forge_full_path},\n\tscope: {self.forge_scope},\n\ttask: {self.test_key}\n\tteardown {self._teardown}"
        )
        try:
            teardown_start_time = time.time()
            if self._exec_id is not None and self._forge.teardown(
                self._exec_id
            ):
                logger.info(
                    f"Forge teardown has been executed successfully, time taken {time.time() - teardown_start_time} seconds:{self.summary}"
                )
        except Exception as e:
            traceback_info = traceback.format_exc()
            report = f"Forge teardown has failed to execute: {e}{self.summary}\n{traceback_info}"
            logger.error(report)
            self._teardown_errors.append(report)


TaskSetListType = List[Optional[List[FrameworkTask]]]
