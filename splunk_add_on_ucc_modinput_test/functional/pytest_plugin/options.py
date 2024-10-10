def pytest_addoption(parser):
    splunk_group = parser.getgroup(
        "Options for functional test framework for Splunk technical add-ons"
    )

    splunk_group.addoption(
        "--sequential-execution",
        dest="sequential_execution",
        action="store_true",
        default=False,
        help="Use no threading (for debugging)",
    )

    splunk_group.addoption(
        "--fail-with-teardown",
        dest="fail_with_teardown",
        action="store_true",
        default=False,
        help="Fail test if teardown fails",
    )

    splunk_group.addoption(
        "--number-of-threads",
        dest="number_of_threads",
        type=int,
        default=10,
        choices=range(1, 21),
        help="Number of threads to use",
    )
