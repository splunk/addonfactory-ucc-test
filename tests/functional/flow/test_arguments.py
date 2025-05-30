from tests.functional.common import ScenarioTester


def test_arguments(pytester):
    with ScenarioTester(pytester, "arguments") as tester:
        tester.result.assert_outcomes(passed=1)
        tester.framework_log_matcher.no_fnmatch_line(
            "*Traceback (most recent call last):*"
        )
        tester.test_log_matcher.fnmatch_lines(
            [
                "*Splunk client method start*",
                "*Splunk client method complete*",
                "*forge1 test_id=*",
                "*forge1 session_id=*",
                "*forge1 explicit_argument=1",
                "*Vendor client method start, timeout=*",
                "*Vendor client method complete",
                "*forge2 test_id=*",
                "*forge2 session_id=*",
                "*forge2 explicit_argument=2",
                "*test_arguments execution",
            ]
        )


def test_artifactory(pytester):
    with ScenarioTester(pytester, "artifactory") as tester:
        tester.result.assert_outcomes(passed=1)
        tester.framework_log_matcher.no_fnmatch_line(
            "*Traceback (most recent call last):*"
        )
        tester.test_log_matcher.fnmatch_lines(
            [
                "*forge1 artifactory value: forge1",
                "*forge1 overwrite_artifact value: forge1",
                "*forge2 artifactory value: forge2",
                "*forge2 overwrite_artifact value: forge1+forge2",
                "*test_artifactory - test_artifactory execution",
            ]
        )


def test_parametrized(pytester):
    with ScenarioTester(pytester, "parametrized") as tester:
        tester.result.assert_outcomes(passed=2)
        tester.framework_log_matcher.no_fnmatch_line(
            "*Traceback (most recent call last):*"
        )
        tester.test_log_matcher.fnmatch_lines(
            [
                "*forge1 test_id=*, parametrized_param1=param1-1",
                "*forge1 test_id=*, parametrized_param1=param-2",
                "*forge2 test_id=*, parametrized_param2=param2-1",
                "*forge2 test_id=*, parametrized_param2=param2-2",
                "*test_parametrized - test_parametrized test_id=* execution",
                "*test_parametrized - test_parametrized test_id=* execution",
            ]
        )


def test_wrongly_parametrized(pytester):
    with ScenarioTester(pytester, "invalid_parameters") as tester:
        tester.result.stdout.fnmatch_lines(
            "*! _pytest.outcomes.Exit: Errors occurred during test collection. Exiting pytest. !*"  # noqa: E501
        )


def test_probes(pytester):
    with ScenarioTester(pytester, "probes") as tester:
        tester.result.assert_outcomes(passed=1)
        tester.framework_log_matcher.no_fnmatch_line(
            "*Traceback (most recent call last):*"
        )
        tester.test_log_matcher.fnmatch_lines(
            [
                "*forge1 for test_id=* started",
                "*Splunk client method start, timeout=*",
                "*Splunk client method complete",
                "*probe1 for test_id=* is negative",
                "*probe1 for test_id=* is negative",
                "*probe1 for test_id=* has succeeded",
                "*forge2 for test_id=* started, probe1=True",
                "*Vendor client method start, timeout=*",
                "*Vendor client method complete",
                "*probe2 for test_id=* is negative",
                "*probe2 for test_id=* is negative",
                "*probe2 for test_id=* has failed",
                "*test_probes execution started",
            ]
        )
