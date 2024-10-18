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
)

@pytest.hookimpl
def pytest_deselected(items):    
    logger.debug(f"Processing deselected items: {items}")
    if not items:
        return
    
    for item in items:
        test = dependency_manager.tests.lookup_by_function(item._obj)
        if test:
            dependency_manager.unregister_test(test.key)
            logger.info(f"Test {test.full_path} is deselected")        


@pytest.hookimpl
def pytest_collection_modifyitems(session, config, items):
    logger.debug(f"Lookung for forged tests in: {items}")
    dependency_manager.link_pytest_config(config)
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
def pytest_collection_finish(session):
    dependency_manager.start_bootstrap_execution()

@pytest.hookimpl
def pytest_runtest_setup(item: pytest.Item) -> None:
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

    custom_args = test.collect_required_kwargs(session_id=dependency_manager.session_id)
    item.funcargs.update(custom_args)
    logger.info(
        f"pytest_runtest_setup: {item} ==>> {test},\n\tartifacts: {test.artifacts},\n\t_fixtureinfo: {item._fixtureinfo.argnames},\n\tfuncargs={item.funcargs},\n\tvars: {vars(item)}"
    )


@pytest.hookimpl
def pytest_runtest_call(item: pytest.Item) -> None:
    pytest_funcname, _ = _extract_parametrized_data(item)
    test = dependency_manager.find_test(item._obj, pytest_funcname)
    if not test:
        return

    logger.info(f"Executing pytest runtest call step for forged test : {test}")


@pytest.hookimpl
def pytest_runtest_teardown(item: pytest.Item) -> None:
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

    if dependency_manager.fail_with_teardown:
        msg = ""
        for task, error in dependency_manager.test_error_report(test):
            item.add_report_section("call", "error", error)
            msg += (
                f"\n\tforge: {task.forge_full_path}, scope: {task.forge_scope}"
            )

        if msg:
            pytest.fail(f"teardown failed:\n\ttest: {test.key}{msg}")
