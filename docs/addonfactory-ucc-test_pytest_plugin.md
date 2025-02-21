# addonfactory-ucc-test pytest plugin

addonfactory-ucc-test pytest plugin comes with following arguments:

- `--sequential-execution` - use no threading (for debugging)

- `--do-not-fail-with-teardown` - do not fail test if test's teardown fails. By default a test will fail if any of it's forges teardowns fail, even if the test itself passed.

- `--do-not-delete-at-teardown` - do not delete created resoueces at teardown. This flag is for debug purposes. Based on this flag developers can add alternative code to forges, that, for example, would disable imputs instead of deleting them in order to study inputs after tests execution.

- `--number-of-threads=[NUMBER_OF_THREADS]` - number of threads to use to execute forges. Allowed range: [10, 20]. Default value: 10.

- `--probe-invoke-interval=[PROBE_INVOKE_INTERVAL]` - interval in seconds used to repeat invocation of yes/no type of probe. Allowed range: [1, 60]. Default value: 5.

- `--probe-wait-timeout=[PROBE_WAIT_TIMEOUT]` - maximum time in seconds given to single probe to turn positive. Allowed range: [60, 600]. Default value: 300.

- `--bootstrap-wait-timeout=[BOOTSTRAP_WAIT_TIMEOUT]` - maximum time in seconds given to all bootstrap tasks to finish. Allowed range: [300, 3600]. Default value: 1800.

- `--attached-tasks-wait-timeout=[ATTACHED_TASKS_WAIT_TIMEOUT]` - maximum time in seconds given to finish all tasks attached to a test. Allowed range: [60, 1200]. Default value: 600.

- `--completion-check-frequency=[COMPLETION_CHECK_FREQUENCY]` - frequency to check that bootstrap or attached tasks bundle has finished to execute. Allowed range: [1, 30]. Default value: 5.
