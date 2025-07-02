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
from typing import List
import pytest
import traceback
from splunk_add_on_ucc_modinput_test.functional import logger
from splunk_add_on_ucc_modinput_test.functional.exceptions import (
    SplTaFwkBaseException,
)
from splunk_add_on_ucc_modinput_test.functional.manager import (
    dependency_manager,
)
from splunk_add_on_ucc_modinput_test.functional.pytest_plugin.utils import (
    _adjust_test_order,
    _debug_log_test_order,
    _log_test_order,
    _collect_skipped_tests,
    _collect_parametrized_tests,
    _extract_parametrized_data,
    _map_forged_tests_to_pytest_items,
    _check_session_terminal_output,
)
from pytest import Session, Config, Item
from typing import Sequence


@pytest.hookimpl
def pytest_deselected(items: Sequence[Item]) -> None:
    logger.debug(f"Processing deselected items: {items}")
    if not items:
        return

    for item in items:
        found_tests_keys = (
            dependency_manager.tests.lookup_by_original_function(item._obj)
        )
        for test_key in found_tests_keys:
            test = dependency_manager.unregister_test(test_key)
            msg = "Test deselection:"
            msg += f'\n\tdeselected: {"Yes" if test else "No"}'
            msg += f"\n\tlookup key: {test_key}"
            msg += f'\n\tpath: {test.full_path if test else "not found"}'
            msg += f'\n\toriginal path: {test.original_full_path if test else "not found"}'
            logger.info(msg)


@pytest.hookimpl
def pytest_collection_modifyitems(
    session: Session, config: Config, items: List[Item]
) -> None:
    dependency_manager.link_pytest_config(config)
    if dependency_manager.collectonly:
        return

    logger.debug(f"Looking for forged tests in: {items}")
    tests2items = _map_forged_tests_to_pytest_items(items)
    if not tests2items:
        logger.debug("No forged tests found, exiting")
        return

    pytest_test_set_keys = set(tests2items.keys())
    dependency_manager.synch_tests_with_pytest_list(pytest_test_set_keys)

    parametrized_tests = _collect_parametrized_tests(items)
    dependency_manager.expand_parametrized_tests(parametrized_tests)
    dependency_manager.dump_tests()

    logger.debug("parametrized_tests: {parametrized_tests}")
    for test_key, param_tests in parametrized_tests.items():
        logger.debug(f"test: {test_key}")
        for test_name, test_kwargs in param_tests:
            logger.debug(
                f"\ttest name: {test_name}, test kwargs: {test_kwargs}"
            )

    skipped_tests = _collect_skipped_tests(items)
    skipped_tests_keys = [test.key for test, _ in skipped_tests]
    dependency_manager.remove_skipped_tests(skipped_tests_keys)

    items[:] = _adjust_test_order(items)

    _debug_log_test_order(items)
    _log_test_order(items)


@pytest.hookimpl
def pytest_collection_finish(session: Session) -> None:
    if dependency_manager.collectonly:
        return
    _check_session_terminal_output(session)

    dependency_manager.start_bootstrap_execution()


@pytest.hookimpl
def pytest_runtest_setup(item: Item) -> None:
    pytest_funcname, _ = _extract_parametrized_data(item)
    test = dependency_manager.find_test(item._obj, pytest_funcname)
    if not test:
        return

    logger.info(
        f"Executing pytest runtest setup step for forged test : {test}"
    )

    try:
        dependency_manager.wait_for_test_bootstrap(test)
        dependency_manager.execute_test_inplace_forges(test)
    except SplTaFwkBaseException as e:
        logger.error(f"Error during test setup: {e}\n{traceback.format_exc()}")
        pytest.fail(str(e))

    global_builtin_args = dependency_manager.get_global_builtin_args(test.key)
    custom_args = test.collect_required_kwargs(global_builtin_args)
    item.funcargs.update(custom_args)
    logger.info(
        f"pytest_runtest_setup: {item} ==>> {test},\n\tartifacts: {test.artifacts},\n\t_fixtureinfo: {item._fixtureinfo.argnames},\n\tfuncargs={item.funcargs},\n\tvars: {vars(item)}"
    )


@pytest.hookimpl
def pytest_runtest_call(item: Item) -> None:
    pytest_funcname, _ = _extract_parametrized_data(item)
    test = dependency_manager.find_test(item._obj, pytest_funcname)
    if not test:
        return

    logger.info(f"Executing pytest runtest call step for forged test : {test}")


@pytest.hookimpl
def pytest_runtest_teardown(item: Item) -> None:
    pytest_funcname, _ = _extract_parametrized_data(item)
    test = dependency_manager.find_test(item._obj, pytest_funcname)
    if not test:
        return

    logger.info(
        f"Executing pytest runtest teardown step for forged test : {test}"
    )
    dependency_manager.teardown_test(test)

    if dependency_manager.check_all_tests_executed():
        dependency_manager.shutdown()

    for task, error in dependency_manager.test_error_report(test):
        item.add_report_section("call", "error", str(error))

    if not dependency_manager.do_not_fail_with_teardown:
        msg = ""
        for task, error in dependency_manager.test_teardown_error_report(test):
            msg += (
                f"\n\tforge: {task.forge_full_path}, scope: {task.forge_scope}"
            )

        if msg:
            pytest.fail(f"teardown failed:\n\ttest: {test.key}{msg}")
