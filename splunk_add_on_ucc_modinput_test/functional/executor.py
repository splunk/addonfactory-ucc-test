import inspect
import time
import types
import threading
import queue
import contextlib
import traceback
import uuid
from splunk_add_on_ucc_modinput_test.functional import logger
from splunk_add_on_ucc_modinput_test.functional.constants import BuiltInArg, ForgeProbe
from splunk_add_on_ucc_modinput_test.functional.exceptions import SplTaFwkWaitForProbeTimeout


def log_exceptions_traceback(fn):
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error executing {fn.__name__}: {e}")
            logger.debug(traceback.format_exc())

        return None

    return wrapper


class FrmwkExecTask:
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
        return callable(self._probe)

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

    def wait_for_probe(self):
        if not self._probe_gen:
            return

        probe_args = self.get_probe_args()
        expire_time = time.time() + ForgeProbe.MAX_WAIT_TIME.value
        for interval in self._probe_gen(**probe_args):
            if time.time() > expire_time:
                msg = f"Test {self.test_key}, forge {self.dep_key}: probe {self._probe.__name__} exceeted {ForgeProbe.MAX_WAIT_TIME.value} seconds timeout"
                raise SplTaFwkWaitForProbeTimeout(msg)
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
                if not FrmwkExecTask.same_args(arg1, arg2):
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
                if not FrmwkExecTask.same_args(v, args2[k]):
                    return False
            return True

        return args1 == args2

    def same_tasks(self, other_task):
        if self.dep_key != other_task.dep_key:
            return False

        args1 = self.get_comparable_args()
        args2 = other_task.get_comparable_args()
        return FrmwkExecTask.same_args(args1, args2)

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
            self.wait_for_probe()
            self._is_executed = True

        logger.debug(
            f"EXECTASK: mark_executed {id(self)} - {self}, dep: {id(self._dep)} - {self._dep} - {self.dep_key}"
        )

    def teardown(self):
        logger.debug(f"EXECTASK: dep {self} teardown {self._teardown}")
        self._dep.teardown(self._exec_id)


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

    def _try_skip_task(self, task_group, test_index, task_index, matched_tasks):
        task = task_group[test_index][task_index]
        same_task = self._find_same_task(task_group, task)
        logger.debug(f"{task.dep_key} SAME TASK IS  {same_task}")
        if same_task:
            logger.debug(f"task_index={task_index} skip task {task.dep_key} execution")
            matched_tasks[(test_index, task_index)] = same_task
        return same_task

    def _process_test_tasks(self, task_group, test_index, test_tasks, matched_tasks):
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
            logger.debug(f"test_index={test_index} push parallel_task {test_tasks}")
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
                if not isinstance(test_result, dict):
                    test_result = {task.default_artifact_name: test_result}
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
        self, task_group, src_test_i, src_task_j, result_collector, matched_tasks
    ):
        src_task = task_group[src_test_i][src_task_j]
        for dst, src in matched_tasks.items():
            if src == (src_test_i, src_task_j):
                dst_test_i, dst_task_j = dst
                result_collector[dst_test_i][dst_task_j] = src_task._result
                task_group[dst_test_i][dst_task_j].reuse_execution(
                    src_task._exec_id, src_task._result
                )
                self._update_test_artifacts(task_group, dst_test_i, result_collector)

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
            result_collector, matched_tasks, tasks_to_run = self._process_task_group(
                task_group
            )
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

        self.monitor_thread = threading.Thread(target=self.monitor, args=(tasks,))
        self.monitor_thread.start()

        self._started = True
        logger.debug("started")

    def shutdown(self):
        self.monitor_queue.put(None)
        self.wait()

    def wait(self):
        self.monitor_thread.join()

    def _collect_results(self, done, result_collector, task_group, matched_tasks):
        while not all(done.values()):
            response = self.monitor_queue.get()
            logger.debug(f"monitor got finished task {response}")
            if response is None:
                logger.debug(f"monitor is interrupted")
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
            result_collector, matched_tasks, tasks_to_run = self._process_task_group(
                task_group
            )
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
