import pytest
from splunk_add_on_ucc_modinput_test.functional import logger
from splunk_add_on_ucc_modinput_test.functional.exceptions import SplTaFwkBaseException
from splunk_add_on_ucc_modinput_test.functional.manager import dependency_manager
from splunk_add_on_ucc_modinput_test.functional.pytest_plugin.utils import (
    _adjust_test_order,
    _debug_log_test_order,
    _log_test_order,
    _collect_skipped_tests,
    _collect_parametrized_tests,
    _extract_parametrized_data,
)


@pytest.hookimpl
def pytest_collection_modifyitems(session, config, items):
    logger.debug(f"start pytest_collection_modifyitems hook: {items}")
    parametrized_tests = _collect_parametrized_tests(items)
    dependency_manager.expand_parametrized_tests(parametrized_tests)
    dependency_manager.dump_tests()

    logger.debug("parametrized_tests: {parametrized_tests}")
    for test_key, param_tests in parametrized_tests.items():
        logger.debug(f"test: {test_key}")
        for test_name, test_kwargs in param_tests:
            logger.debug(f"\ttest name: {test_name}, test kwargs: {test_kwargs}")

    skipped_tests = _collect_skipped_tests(items)

    items[:] = _adjust_test_order(items)

    _debug_log_test_order(items)
    _log_test_order(items)

    deps_mtx = dependency_manager.build_dep_exec_matrix(skipped_tests)
    sequential_execution = config.getvalue("sequential_execution")
    number_of_threads = config.getvalue("number_of_threads")
    dependency_manager.start_dependency_execution(
        deps_mtx, sequential_execution, number_of_threads
    )


@pytest.hookimpl
def pytest_runtest_setup(item: pytest.Item) -> None:
    logger.info(f"pytest_runtest_setup: STARTED {item}")
    pytest_funcname, _ = _extract_parametrized_data(item)
    test = dependency_manager.find_test(item._obj, pytest_funcname)
    if not test:
        logger.info(f"pytest_runtest_setup: {item} NOT FOUND")
        return

    try:
        test.wait_for_dependencies()
    except SplTaFwkBaseException as e:
        pytest.fail(str(e))

    item.funcargs.update(test.collect_required_kwargs())
    logger.info(
        f"pytest_runtest_setup: {item} ==>> {test},\n\tartifacts: {test.artifacts},\n\t_fixtureinfo: {item._fixtureinfo.argnames},\n\tfuncargs={item.funcargs},\n\tvars: {vars(item)}"
    )


@pytest.hookimpl
def pytest_runtest_call(item: pytest.Item) -> None:
    logger.info(f"pytest_runtest_call: STARTED {item}")
    pytest_funcname, _ = _extract_parametrized_data(item)
    test = dependency_manager.find_test(item._obj, pytest_funcname)
    if not test:
        logger.info(f"pytest_runtest_call: {item} NOT FOUND")
        return

    logger.info(f"pytest_runtest_call: {item} ==>> {test}")


@pytest.hookimpl
def pytest_runtest_teardown(item: pytest.Item) -> None:
    logger.info(f"pytest_runtest_teardown: STARTED {item}")
    pytest_funcname, _ = _extract_parametrized_data(item)
    test = dependency_manager.find_test(item._obj, pytest_funcname)
    if not test:
        logger.info(f"pytest_runtest_teardown: {item} NOT FOUND")
        return

    logger.info(f"pytest_runtest_teardown: {item} ==>> {test}")
    dependency_manager.teardown_test(test)
