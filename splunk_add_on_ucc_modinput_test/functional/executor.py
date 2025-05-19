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

from splunk_add_on_ucc_modinput_test.typing import (
    ArtifactsType,
    ExecutableKeyType,
)

import threading
from queue import Queue
import traceback
import time
from dataclasses import dataclass
from typing import Any, Callable, TYPE_CHECKING
from splunk_add_on_ucc_modinput_test.functional import logger
from splunk_add_on_ucc_modinput_test.functional.entities.task import (
    FrameworkTask,
    TaskSetListType,
)
from splunk_add_on_ucc_modinput_test.functional.exceptions import (
    SplTaFwkWaitForDependenciesTimeout,
)

if TYPE_CHECKING:
    from splunk_add_on_ucc_modinput_test.functional.manager import (
        TestDependencyManager,
    )


def log_exceptions_traceback(fn: Callable[..., Any]) -> Callable[..., Any]:
    def wrapper(*args: Any, **kwargs: Any) -> Any | None:
        try:
            logger.debug(f"{fn.__name__} executor is about to start")
            return fn(*args, **kwargs)
        except Exception as e:
            logger.error(f"{fn.__name__} executor has failed with error: {e}")
            logger.debug(traceback.format_exc())
        finally:
            logger.debug(f"{fn.__name__} executor has stopped")
        return None

    return wrapper


class TaskGroupProcessor:
    @dataclass
    class Job:
        test_index: int
        task_index: int
        task: FrameworkTask

        @property
        def id(self) -> tuple[int, int]:
            return self.test_index, self.task_index

    def __init__(
        self,
        group: TaskSetListType,
        global_builtin_args_factory: Callable[
            [ExecutableKeyType], ArtifactsType
        ],
    ) -> None:
        self._global_builtin_args_factory = global_builtin_args_factory
        self._task_group: TaskSetListType = group
        self._jobs: list[TaskGroupProcessor.Job] = []
        self._matched_tasks: dict[tuple[int, int], tuple[int, int]] = {}
        self._result_collector: list[list[object | None] | None] = [
            None
        ] * len(self._task_group)
        self._done: dict[tuple[int, int], bool] = {}

        self._build_task_list()

    def _build_task_list(self) -> None:
        logger.debug(f"\npush task group {self._task_group}")

        for test_index, test_tasks in enumerate(self._task_group):
            logger.debug(
                f"test_index={test_index} push parallel_task {test_tasks}"
            )
            if test_tasks is not None:
                self._result_collector[test_index] = [None] * len(test_tasks)
                self._jobs += self._process_test_tasks(test_index, test_tasks)

        for job in self._jobs:
            self._done[job.id] = False

    @property
    def jobs(self) -> list[Job]:
        return self._jobs

    @property
    def all_tasks_done(self) -> bool:
        return all(self._done.values())

    def _process_test_tasks(
        self, test_index: int, test_tasks: list[FrameworkTask]
    ) -> list[Job]:
        processed_tasks = []
        for task_index, task in enumerate(test_tasks):
            try:
                task.prepare_forge_call_args(
                    self._global_builtin_args_factory(task.test_key)
                )
            except Exception as e:
                task.mark_as_failed(e, "Failed to prepare forge call args")
            else:
                if not self._try_skip_task(test_index, task_index):
                    job = self.Job(test_index, task_index, task)
                    processed_tasks.append(job)

        return processed_tasks

    def _get_task(self, test_index: int, task_index: int) -> FrameworkTask:
        test_tasks = self._task_group[test_index]
        assert test_tasks is not None, "test_tasks must be valid"
        return test_tasks[task_index]

    def _try_skip_task(
        self, test_index: int, task_index: int
    ) -> tuple[int, int] | None:
        task = self._get_task(test_index, task_index)
        same_task = self._find_same_task(task)
        logger.debug(f"{task.forge_key} SAME TASK IS  {same_task}")
        if same_task:
            logger.debug(
                f"task_index={task_index} skip task {task.forge_key} execution"
            )
            self._matched_tasks[(test_index, task_index)] = same_task
        return same_task

    def _find_same_task(self, task: FrameworkTask) -> tuple[int, int] | None:
        for i, test_tasks in enumerate(self._task_group):
            if test_tasks is None:
                continue
            for j, t in enumerate(test_tasks):
                if task is t:
                    return None
                if task.same_tasks(t):
                    return i, j
        return None

    def _update_test_artifacts(self, test_index: int) -> None:
        test_results = self._result_collector[test_index]
        if test_results:
            for task_index, test_result in enumerate(test_results):
                task = self._get_task(test_index, task_index)
                logger.debug(
                    f"TEST RESULT {test_result} is dict - {isinstance(test_result, dict)}, test {task.test_key}, dep: {task.forge_key}, result {task.result}"
                )
                test_result = task.make_kwarg(test_result)
                task.update_test_artifacts(test_result)
                logger.debug(
                    f"ARTIFACTS UPDATED dep: {task.forge_key}, test {task.test_key}, artifacts: {task._test.artifacts}"
                )

    def _copy_result_to_matching_tasks(
        self, src_test_i: int, src_task_j: int
    ) -> None:
        src_task = self._get_task(src_test_i, src_task_j)
        for dst, src in self._matched_tasks.items():
            if src == (src_test_i, src_task_j):
                dst_test_i, dst_task_j = dst

                row = self._result_collector[dst_test_i]
                if row is not None:
                    row[dst_task_j] = src_task._result

                    dst_task = self._get_task(dst_test_i, dst_task_j)
                    if src_task._exec_id is not None:
                        dst_task.reuse_forge_execution(
                            src_task._exec_id,
                            src_task._result,
                            src_task._setup_errors,
                        )
                        dst_task.mark_as_executed()
                        self._update_test_artifacts(dst_test_i)

    def process_response(self, job: Job) -> None:
        finished_task = self._get_task(job.test_index, job.task_index)
        assert finished_task is job.task, "Task is not the same!"
        logger.debug(
            f"manager got finished task {job.id}, TEST KEY: {finished_task.test_key}, DEP KEY: {finished_task.forge_key}, DEP RES: {finished_task.result}, RES {job.task.result}"
        )

        row = self._result_collector[job.test_index]
        if row is not None:
            row[job.task_index] = job.task.result
            self._update_test_artifacts(job.test_index)
            self._copy_result_to_matching_tasks(job.test_index, job.task_index)
            self._done[job.id] = True
            logger.debug(
                f"manager is waiting for tasks {self._done}, results: {self._result_collector}"
            )


class FrmwkExecutorBase:
    def __init__(self, manager: TestDependencyManager) -> None:
        self._manager = manager

    def shutdown(self) -> None:
        pass

    def wait(self, is_bootstrap: bool) -> None:
        pass

    def global_builtin_args_factory(
        self, test_key: ExecutableKeyType
    ) -> ArtifactsType:
        return self._manager.get_global_builtin_args(test_key)

    def _execute_request(
        self, job: TaskGroupProcessor.Job, worker_id: int = 0
    ) -> None:
        try:
            task_info = f"{job.id}, task: {id(job.task)} - {job.task}, dep: {id(job.task._forge)} - {job.task._forge} - {job.task.forge_key}, call_args: {job.task._forge_kwargs}"
            logger.debug(f"worker {worker_id}, task started {task_info}")
            job.task.execute()
        except Exception as e:
            logger.debug(
                f"worker {worker_id}, task failed {task_info} with error {e}\n{traceback.format_exc()}"
            )
        else:
            logger.debug(
                f"worker {worker_id}, task finished {task_info} with result: {job.task.result}"
            )


class FrmwkSequentialExecutor(FrmwkExecutorBase):
    def start(self, tasks: list[TaskSetListType]) -> None:
        logger.debug(f"sequential executor has started with tasks {tasks}")
        for task_group in tasks:
            proc = TaskGroupProcessor(
                task_group, self.global_builtin_args_factory
            )
            for job in proc.jobs:
                self._execute_request(job)
                proc.process_response(job)

        logger.debug("sequential executor has finished")


class FrmwkParallelExecutor(FrmwkExecutorBase):
    def __init__(
        self, manager: TestDependencyManager, worker_count: int = 10
    ) -> None:
        super().__init__(manager)
        self.worker_count = worker_count
        self.task_queue: Queue[TaskGroupProcessor.Job | None] = Queue()
        self._manager_queue: Queue[
            list[TaskSetListType] | TaskGroupProcessor.Job | None
        ] = Queue()
        self._is_free: threading.Event = threading.Event()
        self.deploy()

    def deploy(self) -> None:
        self.threads = [
            threading.Thread(target=self.worker_thread, args=(index,))
            for index in range(self.worker_count)
        ]

        for thread in self.threads:
            thread.start()

        self._manager_thread = threading.Thread(target=self.manager_thread)
        self._manager_thread.start()

        logger.debug("deployed")
        self._is_free.set()
        logger.debug("FrmwkParallelExecutor is set free")

    def wait(self, is_bootstrap: bool = True) -> None:
        if is_bootstrap:
            wait_timeout = self._manager.bootstrap_wait_timeout
            task_type = "bootstrap"
        else:
            wait_timeout = self._manager.attached_tasks_wait_timeout
            task_type = "attached"

        expiration = time.time() + wait_timeout
        while not self._is_free.wait(self._manager.completion_check_frequency):
            if time.time() > expiration:
                msg = f"Waiting for executor to process all {task_type} tasks exceeded timeout {wait_timeout} seconds."
                logger.error(msg)
                raise SplTaFwkWaitForDependenciesTimeout(msg)
            logger.debug(
                f"Still waiting for executor to process all {task_type} tasks"
            )

    def start(self, tasks: list[TaskSetListType]) -> None:
        logger.debug("FrmwkParallelExecutor::start - wait for previoues tasks")
        self.wait()
        logger.debug(
            "FrmwkParallelExecutor::start - executer is about to set busy"
        )
        self._is_free.clear()
        logger.debug("FrmwkParallelExecutor is set busy")
        logger.debug("FrmwkParallelExecutor::start - sending tasks to manager")
        self._manager_queue.put(tasks)
        logger.debug("started")

    def shutdown(self) -> None:
        logger.debug("Sending shutdown command to executor...")
        self._manager_queue.put(None)
        logger.debug("Waiting for executor to shutdown...")
        self._manager_thread.join()
        logger.info("Executor has shutdown.")

    def _receive_tasks(
        self,
    ) -> tuple[bool, list[TaskSetListType] | TaskGroupProcessor.Job | None]:
        logger.debug(
            "FrmwkParallelExecutor::_receive_tasks - set waiting for tasks"
        )
        tasks = self._manager_queue.get()
        logger.debug(
            f"FrmwkParallelExecutor::_receive_tasks - got tasks: {tasks}"
        )
        self._manager_queue.task_done()
        logger.debug("FrmwkParallelExecutor::_receive_tasks - queue task done")
        if tasks is None:
            return True, []
        return False, tasks

    def _collect_results(self, proc: TaskGroupProcessor) -> bool:
        while not proc.all_tasks_done:
            job = self._manager_queue.get()
            logger.debug(f"manager got finished task {job}")
            if job is None:
                logger.debug("manager is interrupted")
                return True

            if isinstance(job, TaskGroupProcessor.Job):
                proc.process_response(job)
                self._manager_queue.task_done()

        return False

    @log_exceptions_traceback
    def manager_thread(self) -> None:
        logger.debug("manager has started")
        interrupted = False
        while not interrupted:
            interrupted, tasks = self._receive_tasks()
            logger.debug(f"manager got tasks {tasks}")
            if isinstance(tasks, list):
                for task_group in tasks:
                    proc = TaskGroupProcessor(
                        task_group, self.global_builtin_args_factory
                    )
                    for job in proc.jobs:
                        self.task_queue.put(job)

                    interrupted = self._collect_results(proc)
                    if interrupted:
                        break

            self._is_free.set()
            logger.debug("FrmwkParallelExecutor is set free")

        for _ in self.threads:
            self.task_queue.put(None)

        for thread in self.threads:
            thread.join()

        logger.debug("manager has finished")

    @log_exceptions_traceback
    def worker_thread(self, wid: int) -> None:
        while True:
            job = self.task_queue.get()
            logger.debug(f"worker {wid} task recieved {job}")
            if job is None:
                break

            self._execute_request(job, wid)
            self.task_queue.task_done()
            self._manager_queue.put(job)
