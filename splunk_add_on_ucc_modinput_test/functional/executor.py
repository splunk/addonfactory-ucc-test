import threading
import queue
import traceback
from splunk_add_on_ucc_modinput_test.functional import logger


def log_exceptions_traceback(fn):
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error executing {fn.__name__}: {e}")
            logger.debug(traceback.format_exc())

        return None

    return wrapper


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

    def _find_same_task(self, task_group, task):
        for i, test_tasks in enumerate(task_group):
            if test_tasks is None:
                continue
            for j, t in enumerate(test_tasks):
                if task is t:
                    return None
                if task.same_tasks(t):
                    return i, j
        return None

    def _try_skip_task(
        self, task_group, test_index, task_index, matched_tasks
    ):
        task = task_group[test_index][task_index]
        same_task = self._find_same_task(task_group, task)
        logger.debug(f"{task.dep_key} SAME TASK IS  {same_task}")
        if same_task:
            logger.debug(
                f"task_index={task_index} skip task {task.dep_key} execution"
            )
            matched_tasks[(test_index, task_index)] = same_task
        return same_task

    def _process_test_tasks(
        self, task_group, test_index, test_tasks, matched_tasks
    ):
        processed_tasks = []
        for task_index, task in enumerate(test_tasks):
            task.prepare_forge_call_args(
                splunk_client=self.manager.create_splunk_client(),
                vendor_client=self.manager.create_vendor_client(),
            )

            if not self._try_skip_task(
                task_group, test_index, task_index, matched_tasks
            ):
                request = (test_index, task_index, task)
                processed_tasks.append(request)

        return processed_tasks

    def _process_task_group(self, task_group):
        tasks_to_run = []
        logger.debug(f"\npush task group {task_group}")
        matched_tasks = {}
        result_collector = [None] * len(task_group)

        for test_index, test_tasks in enumerate(task_group):
            logger.debug(
                f"test_index={test_index} push parallel_task {test_tasks}"
            )
            if test_tasks is not None:
                result_collector[test_index] = [None] * len(test_tasks)
                if test_tasks is not None:
                    tasks_to_run += self._process_test_tasks(
                        task_group, test_index, test_tasks, matched_tasks
                    )

        return result_collector, matched_tasks, tasks_to_run

    def _update_test_artifacts(self, task_group, test_index, result_collector):
        test_results = result_collector[test_index]
        if test_results:
            for test_tasks, test_result in enumerate(test_results):
                task = task_group[test_index][test_tasks]
                logger.debug(
                    f"TEST RESULT {test_result} is dict - {isinstance(test_result, dict)}, test {task.test_key}, dep: {task.dep_key}, result {task.result}"
                )
                test_result = task.make_kwarg(test_result)
                task.update_test_artifacts(test_result)
                logger.debug(
                    f"ARTIFACTS UPDATED dep: {task.dep_key}, test {task.test_key}, artifacts: {task._test.artifacts}"
                )

    def _execute_request(self, request, executor_id):
        try:
            test_index, task_index, task = request
            logger.debug(
                f"worker {executor_id} task started {test_index}:{task_index}, task: {id(task)} - {task}, dep: {id(task._dep)} - {task._dep} - {task.dep_key}, call_args: {task._call_args}"
            )
            task.execute()
            logger.debug(
                f"worker {executor_id} task finished {test_index}:{task_index}, task: {id(task)} - {task}, dep: {id(task._dep)} - {task._dep} - {task.dep_key}, call_args: {task._call_args}, result: {task.result}"
            )
        except Exception as e:
            logger.debug(traceback.format_exc())
            logger.error(
                f"worker {executor_id} task FAILED {test_index}:{task_index}, {e}"
            )
            task.completed_with_error(e)

    def _copy_result_to_matching_tasks(
        self,
        task_group,
        src_test_i,
        src_task_j,
        result_collector,
        matched_tasks,
    ):
        src_task = task_group[src_test_i][src_task_j]
        for dst, src in matched_tasks.items():
            if src == (src_test_i, src_task_j):
                dst_test_i, dst_task_j = dst
                result_collector[dst_test_i][dst_task_j] = src_task._result
                task_group[dst_test_i][dst_task_j].reuse_execution(
                    src_task._exec_id, src_task._result
                )
                self._update_test_artifacts(
                    task_group, dst_test_i, result_collector
                )

    def _process_response(
        self, response, result_collector, task_group, matched_tasks, done=None
    ):
        test_index, task_index, result = response
        finished_task = task_group[test_index][task_index]
        logger.debug(
            f"monitor got finished task {test_index}, {task_index}, TEST KEY: {finished_task.test_key}, DEP KEY: {finished_task.dep_key}, DEP RES: {finished_task.result}, RES {result}"
        )

        result_collector[test_index][task_index] = result
        self._update_test_artifacts(task_group, test_index, result_collector)
        self._copy_result_to_matching_tasks(
            task_group, test_index, task_index, result_collector, matched_tasks
        )
        if done:
            done[(test_index, task_index)] = True
        logger.debug(
            f"monitor is waiting for tasks {done}, results: {result_collector}"
        )


class FrmwkSequentialExecutor(FrmwkExecutorBase):
    def start(self, tasks):
        super().start(tasks)

        logger.debug("monitor has started")
        for task_group in tasks:
            (
                result_collector,
                matched_tasks,
                tasks_to_run,
            ) = self._process_task_group(task_group)
            for request in tasks_to_run:
                test_index, task_index, task = request
                self._execute_request(request, 0)
                response = (test_index, task_index, task.result)
                self._process_response(
                    response, result_collector, task_group, matched_tasks
                )

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

    def _collect_results(
        self, done, result_collector, task_group, matched_tasks
    ):
        while not all(done.values()):
            response = self.monitor_queue.get()
            logger.debug(f"monitor got finished task {response}")
            if response is None:
                logger.debug("monitor is interrupted")
                return True

            self._process_response(
                response, result_collector, task_group, matched_tasks, done
            )
            self.monitor_queue.task_done()
        return False

    @log_exceptions_traceback
    def monitor(self, tasks):
        logger.debug("monitor has started")
        for task_group in tasks:
            (
                result_collector,
                matched_tasks,
                tasks_to_run,
            ) = self._process_task_group(task_group)
            done = {}
            for request in tasks_to_run:
                test_index, task_index, _ = request
                done[(test_index, task_index)] = False
                self.task_queue.put(request)

            interrupted = self._collect_results(
                done, result_collector, task_group, matched_tasks
            )
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
            request = self.task_queue.get()
            logger.debug(f"worker {wid} task recieved {request}")
            if request is None:
                break

            test_index, task_index, task = request
            self._execute_request(request, wid)
            self.task_queue.task_done()
            self.monitor_queue.put((test_index, task_index, task.result))
