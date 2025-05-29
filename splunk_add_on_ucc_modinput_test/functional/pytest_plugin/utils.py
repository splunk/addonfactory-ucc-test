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
import pytest
from typing import Any, Dict, List, Tuple
from splunk_add_on_ucc_modinput_test.functional import logger
from splunk_add_on_ucc_modinput_test.functional.entities.test import (
    FrameworkTest,
)
from splunk_add_on_ucc_modinput_test.functional.manager import (
    dependency_manager,
)
from pytest import Item, Session
from _pytest.mark.structures import Mark

from splunk_add_on_ucc_modinput_test.typing import ExecutableKeyType


def _extract_parametrized_data(pyfuncitem: Item) -> Tuple[str, Any]:
    callspec_params = {}
    if hasattr(pyfuncitem, "callspec"):
        callspec_params = pyfuncitem.callspec.params
    return pyfuncitem.keywords.node.name, callspec_params


def _map_forged_tests_to_pytest_items(
    items: List[Item],
) -> Dict[ExecutableKeyType, Item]:
    forged_tests = {}
    for item in items:
        test = dependency_manager.tests.lookup_by_function(item._obj)
        if test:
            forged_tests[test.key] = item
    return forged_tests


def _collect_parametrized_tests(
    items: List[Item],
) -> Dict[ExecutableKeyType, List[Tuple[str, Any]]]:
    parametrized_tests: Dict[ExecutableKeyType, List[Tuple[str, Any]]] = {}
    for item in items:
        parametrized_markers = [
            marker
            for marker in item.own_markers
            if marker.name == "parametrize"
        ]
        if parametrized_markers:
            test = dependency_manager.tests.lookup_by_function(item._obj)
            if test:
                logger.debug(
                    f"parametrized_item: {item},\n\tvars: {vars(item)},\n\tnode: {item.keywords.node},\n\tnode vars: {vars(item.keywords.node)}\n\tvars(test): {vars(test)}"
                )
                if test.key not in parametrized_tests:
                    parametrized_tests[test.key] = []
                parametrized_tests[test.key].append(
                    _extract_parametrized_data(item)
                )

    logger.debug(f"Collected parametrized_tests: {len(parametrized_tests)}")
    for test_key, param_tests in parametrized_tests.items():
        logger.debug(f"\ttest: {test_key}")
        for test_name, test_kwargs in param_tests:
            logger.debug(
                f"\t\ttest name: {test_name}, test kwargs: {test_kwargs}"
            )
    return parametrized_tests


def _collect_skipped_tests(
    items: List[Item],
) -> List[Tuple[FrameworkTest, List[Mark]]]:
    skip_tests = []
    for item in items:
        skipped_markers = [
            marker for marker in item.own_markers if marker.name == "skip"
        ]
        if skipped_markers:
            pytest_funcname, _ = _extract_parametrized_data(item)
            test = dependency_manager.find_test(item._obj, pytest_funcname)
            logger.debug(f"_collect_skipped_tests: {item} ==>> {test}")
            if test:
                skip_tests.append((test, skipped_markers))
    return skip_tests


def _adjust_test_order(items: List[Item]) -> List[Item]:
    tests = []
    logger.debug("Initial test order:")
    for item in items:
        pytest_funcname, _ = _extract_parametrized_data(item)
        test = dependency_manager.find_test(item._obj, pytest_funcname)
        if test:
            logger.debug(f"Item: {item} -> {test.key}")
            ip_tasks, bs_tasks = dependency_manager.tasks.get_tasks_by_type(
                test.key
            )
            tests.append((item, (int(len(ip_tasks) > 0), len(bs_tasks))))
        else:
            tests.append((item, (-1, 0)))

    sorted_items = sorted(tests, key=lambda v: v[1])
    return [item for item, _ in sorted_items]


def _debug_log_test_order(items: List[Item]) -> None:
    logger.debug("Adjusted test order:")
    for item in items:
        pytest_funcname, _ = _extract_parametrized_data(item)
        test = dependency_manager.find_test(item._obj, pytest_funcname)
        logger.debug(f"{type(item)}, {item} => {vars(item)}")
        if test:
            logger.debug(f"{item} -> {test.key}: {test.forges}")
        else:
            logger.debug(f"NOT FOUND: {item}, {pytest_funcname} ")


def _log_test_order(items: List[Item]) -> None:
    order = "\nTest execution order:\n"
    for index, item in enumerate(items):
        pytest_funcname, _ = _extract_parametrized_data(item)
        test = dependency_manager.find_test(item._obj, pytest_funcname)
        if test:
            order += f"{index}. {'::'.join(test.key)}\n"
            test_tasks = dependency_manager.tasks.get_bootstrap_tasks(test.key)
            for level, tasks in enumerate(test_tasks):
                order += f"\tLevel {level}\n"
                if tasks is not None:
                    for task in tasks:
                        order += f"\t\t{task.forge_full_path}\n"
        else:
            logger.debug(f"NOT FOUND: {item}, {pytest_funcname} ")

    logger.info(order)


def _check_session_terminal_output(session: Session) -> None:
    # Access the terminal reporter to check for collection errors
    terminal_reporter = session.config.pluginmanager.get_plugin(
        "terminalreporter"
    )
    if terminal_reporter and "error" in terminal_reporter.stats:
        errors = terminal_reporter.stats["error"]
        if errors:
            logger.error("Errors occurred during test collection:")
            for error in errors:
                logger.error(error.longrepr)
            pytest.exit(
                "Errors occurred during test collection. Exiting pytest.",
                returncode=1,
            )
