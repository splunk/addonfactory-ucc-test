from __future__ import annotations
import os
import time
from datetime import datetime
from copy import copy
from fnmatch import fnmatch
from pytest import Pytester, LineMatcher


class LineMatcher2(LineMatcher):
    def fnfilter_lines(self, filter_string):
        filtered = []

        for line in self.lines:
            if fnmatch(line, filter_string):
                filtered.append(copy(line))

        return LineMatcher2(filtered)


class ScenarioTester:
    FRAMEWORK_LOG_FILE = "splunk-add-on-ucc-modinput-test-functional.log"
    TESTS_LOG_FILE = "ucc_modinput_test.log"
    SCENARIO_LOCATION = "tests/functional/flow/scenarios"
    PROJECT_FOLDER = os.getcwd()

    def __init__(self, pytester: Pytester, scenario: str) -> None:
        self.pytester = pytester
        self.scenario = scenario

        self._framework_log_path = os.path.join(
            self.PROJECT_FOLDER, self.FRAMEWORK_LOG_FILE
        )
        self.framework_log_matcher: LineMatcher2 | None = None

        self._test_log_path = os.path.join(
            self.PROJECT_FOLDER, self.TESTS_LOG_FILE
        )
        self.test_log_matcher: LineMatcher2 | None = None

    @staticmethod
    def _load_log_time_frame(file_name, start, stop):
        with open(file_name) as f:
            lines = f.read().splitlines()
        result = []
        in_frame = False
        for line in lines:
            time_prefix = line[:23]
            try:
                record_time = datetime.strptime(
                    time_prefix, "%Y-%m-%d %H:%M:%S,%f"
                )
                if start <= record_time.timestamp() <= stop:
                    in_frame = True
                    result.append(line)
                elif in_frame:
                    in_frame = False
                    break
            except ValueError:
                if in_frame:
                    result.append(line)

        return result

    def _load_framework_log(self, start: float, stop: float) -> None:
        lines = self._load_log_time_frame(
            self._framework_log_path, start, stop
        )
        self.framework_log_matcher = LineMatcher2(lines)

    def _load_test_log(self, start, stop):
        lines = self._load_log_time_frame(self._test_log_path, start, stop)
        self.test_log_matcher = LineMatcher2(lines)

    def _load_scenario(self):
        full_path = os.path.join(
            self.PROJECT_FOLDER, self.SCENARIO_LOCATION, f"{self.scenario}.py"
        )
        with open(full_path) as f:
            return f.read()

    def __enter__(self):
        content = self._load_scenario()
        self.test_folder = self.pytester.makepyfile(content)
        start_time = time.time()
        self.result = self.pytester.runpytest_inprocess()
        stop_time = time.time()
        self._load_framework_log(start_time, stop_time)
        self._load_test_log(start_time, stop_time)

        return self

    def __exit__(self, type, value, traceback):
        pass
