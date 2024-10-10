import threading
import queue
import traceback
from typing import Any
from dataclasses import dataclass
from splunk_add_on_ucc_modinput_test.functional import logger
from splunk_add_on_ucc_modinput_test.functional.entities.task import FrameworkTask


def log_exceptions_traceback(fn):
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error executing {fn.__name__}: {e}")
            logger.debug(traceback.format_exc())

        return None

    return wrapper

class TaskGroupProcessor:
    @dataclass
    class Job:
        test_index: int
        task_index: int
        task: FrameworkTask

        @property
        def id(self):
            return self.test_index, self.task_index

    def __init__(self, group, clients_factory):
        self._clients_factory = clients_factory
        self._task_group = group
        self._jobs = []
        self._matched_tasks = {}
        self._result_collector = [None] * len(self._task_group)
        self._done = {}
        
        self._build_task_list()
        
    def _build_task_list(self):
        logger.debug(f"\npush task group {self._task_group}")
        
        for test_index, test_tasks in enumerate(self._task_group):
            logger.debug(
                f"test_index={test_index} push parallel_task {test_tasks}"
            )
            if test_tasks is not None:
                self._result_collector[test_index] = [None] * len(test_tasks)
                if test_tasks is not None:
                    self._jobs += self._process_test_tasks(test_index, test_tasks)
        
        for job in self._jobs:
            self._done[job.id] = False

    @property
    def jobs(self):
        return self._jobs

    @property
    def all_tasks_done(self):
        return all(self._done.values())

    def _process_test_tasks(self, test_index, test_tasks):
        processed_tasks = []
        for task_index, task in enumerate(test_tasks):
            task.prepare_forge_call_args(**self._clients_factory())

            if not self._try_skip_task(test_index, task_index):
                job = self.Job(test_index, task_index, task)
                processed_tasks.append(job)

        return processed_tasks

    def _try_skip_task(self, test_index, task_index):
        task = self._task_group[test_index][task_index]
        same_task = self._find_same_task(task)
        logger.debug(f"{task.forge_key} SAME TASK IS  {same_task}")
        if same_task:
            logger.debug(
                f"task_index={task_index} skip task {task.forge_key} execution"
            )
            self._matched_tasks[(test_index, task_index)] = same_task
        return same_task

    def _find_same_task(self, task):
        for i, test_tasks in enumerate(self._task_group):
            if test_tasks is None:
                continue
            for j, t in enumerate(test_tasks):
                if task is t:
                    return None
                if task.same_tasks(t):
                    return i, j
        return None

    def _update_test_artifacts(self, test_index):
        test_results = self._result_collector[test_index]
        if test_results:
            for task_index, test_result in enumerate(test_results):
                task = self._task_group[test_index][task_index]
                logger.debug(
                    f"TEST RESULT {test_result} is dict - {isinstance(test_result, dict)}, test {task.test_key}, dep: {task.forge_key}, result {task.result}"
                )
                test_result = task.make_kwarg(test_result)
                task.update_test_artifacts(test_result)
                logger.debug(
                    f"ARTIFACTS UPDATED dep: {task.forge_key}, test {task.test_key}, artifacts: {task._test.artifacts}"
                )

    def _copy_result_to_matching_tasks(self, src_test_i, src_task_j):
        src_task = self._task_group[src_test_i][src_task_j]
        for dst, src in self._matched_tasks.items():
            if src == (src_test_i, src_task_j):
                dst_test_i, dst_task_j = dst
                self._result_collector[dst_test_i][dst_task_j] = src_task._result
                dst_task = self._task_group[dst_test_i][dst_task_j]
                dst_task.reuse_forge_execution(
                    src_task._exec_id, src_task._result, src_task._errors
                )
                dst_task.mark_as_executed()
                self._update_test_artifacts(dst_test_i)
                

    def process_response(self, job):
        finished_task = self._task_group[job.test_index][job.task_index]
        assert finished_task is job.task, "Task is not the same!"
        logger.debug(
            f"monitor got finished task {job.id}, TEST KEY: {finished_task.test_key}, DEP KEY: {finished_task.forge_key}, DEP RES: {finished_task.result}, RES {job.task.result}"
        )

        self._result_collector[job.test_index][job.task_index] = job.task.result
        self._update_test_artifacts(job.test_index)
        self._copy_result_to_matching_tasks(job.test_index, job.task_index)
        self._done[job.id] = True
        logger.debug(
            f"monitor is waiting for tasks {self._done}, results: {self._result_collector}"
        )

class FrmwkExecutorBase:
    def __init__(self, manager):
        self.manager = manager
        self._started = False

    @property
    def is_started(self):
        return self._started

    def start(self, tasks):
        self._tasks = tasks
        self._started = True
        logger.debug("started")

    def shutdown(self):
        pass

    def wait(self):
        pass

    def clients_factory(self):
        return dict(
            splunk_client=self.manager.create_splunk_client(),
            vendor_client=self.manager.create_vendor_client(),
        )

    def _execute_request(self, job, worker_id=0):
        try:
            task_info = f"{job.id}, task: {id(job.task)} - {job.task}, dep: {id(job.task._forge)} - {job.task._forge} - {job.task.forge_key}, call_args: {job.task._forge_kwargs}"
            logger.debug(
                f"worker {worker_id}, task started {task_info}"
            )
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
    def start(self, tasks):
        super().start(tasks)

        logger.debug("monitor has started")
        for task_group in tasks:
            proc = TaskGroupProcessor(task_group, self.clients_factory)
            for job in proc.jobs:
                self._execute_request(job)
                proc.process_response(job)

        logger.debug("monitor has finished")


class FrmwkParallelExecutor(FrmwkExecutorBase):
    def __init__(self, manager, worker_count=10):
        super().__init__(manager)
        self.worker_count = worker_count
        self.task_queue = queue.Queue()
        self.monitor_queue = queue.Queue()

    def start(self, tasks):
        super().start(tasks)
        self.threads = [
            threading.Thread(target=self.worker, args=(index,))
            for index in range(self.worker_count)
        ]
        [thread.start() for thread in self.threads]

        self.monitor_thread = threading.Thread(
            target=self.monitor, args=(tasks,)
        )
        self.monitor_thread.start()

        self._started = True
        logger.debug("started")

    def shutdown(self):
        self.monitor_queue.put(None)
        self.wait()

    def wait(self):
        self.monitor_thread.join()

    def _collect_results(self, proc):
        while not proc.all_tasks_done:
            job = self.monitor_queue.get()
            logger.debug(f"monitor got finished task {job}")
            if job is None:
                logger.debug("monitor is interrupted")
                return True

            proc.process_response(job)
            self.monitor_queue.task_done()
            
        return False

    @log_exceptions_traceback
    def monitor(self, tasks):
        logger.debug("monitor has started")
        for task_group in tasks:
            proc = TaskGroupProcessor(task_group, self.clients_factory)
            for job in proc.jobs:
                self.task_queue.put(job)

            interrupted = self._collect_results(proc)
            if interrupted:
                break

        for _ in self.threads:
            self.task_queue.put(None)

        for thread in self.threads:
            thread.join()

        logger.debug("monitor has finished")

    @log_exceptions_traceback
    def worker(self, wid):
        while True:
            job = self.task_queue.get()
            logger.debug(f"worker {wid} task recieved {job}")
            if job is None:
                break

            self._execute_request(job, wid)
            self.task_queue.task_done()
            self.monitor_queue.put(job)
