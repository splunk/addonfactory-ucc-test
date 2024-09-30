from splunk_add_on_ucc_modinput_test.functional import logger
from splunk_add_on_ucc_modinput_test.functional.manager import (
    dependency_manager,
)


def _extract_parametrized_data(pyfuncitem):
    callspec_params = {}
    if hasattr(pyfuncitem, "callspec"):
        callspec_params = pyfuncitem.callspec.params
    return pyfuncitem.keywords.node.name, callspec_params

def _map_items_to_forged_tests(items):
    forged_tests = {}
    for item in items:
        test = dependency_manager.tests.lookup_by_function(item._obj)
        if test:
            forged_tests[test.key] = item
    return forged_tests


def _collect_parametrized_tests(items):
    parametrized_tests = {}
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


def _collect_skipped_tests(items):
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


def _adjust_test_order(items):
    tests = []
    logger.debug("Initial test order:")
    for item in items:
        pytest_funcname, _ = _extract_parametrized_data(item)
        test = dependency_manager.find_test(item._obj, pytest_funcname)
        if test:
            logger.debug(f"Item: {item} -> {test.key}")
            test.dump()
            tests.append((item, len(test.dep_tasks)))
        else:
            tests.append((item, 0))

    sorted_items = sorted(tests, key=lambda v: v[1])

    reordered_items = [item for item, _ in sorted_items]
    return reordered_items


def _debug_log_test_order(items):
    logger.debug("Adjusted test order:")
    for item in items:
        pytest_funcname, _ = _extract_parametrized_data(item)
        test = dependency_manager.find_test(item._obj, pytest_funcname)
        logger.debug(f"{type(item)}, {item} => {vars(item)}")
        if test:
            logger.debug(f"{item} -> {test.key}: {test.bound_deps}")
            test.dump()
        else:
            logger.debug(f"NOT FOUND: {item}, {pytest_funcname} ")


def _log_test_order(items):
    order = "\nTest execution order:\n"
    for index, item in enumerate(items):
        pytest_funcname, _ = _extract_parametrized_data(item)
        test = dependency_manager.find_test(item._obj, pytest_funcname)
        if test:
            order += f"{index}. {'::'.join(test.key)}\n"
            for level, tasks in enumerate(test.dep_tasks):
                order += f"\tLevel {level}\n"
                for task in tasks:
                    order += f"\t\t{'::'.join(task.dep_key[:2])}\n"
        else:
            logger.debug(f"NOT FOUND: {item}, {pytest_funcname} ")

    logger.info(order)
