class PytestConfigAdapter:
    def __init__(self, pytest_config=None):
        self._pytest_config = pytest_config
    
    def link_pytest_config(self, pytest_config):
        self._pytest_config = pytest_config

    @property
    def pytest_config(self):
        return self._pytest_config
    
    @property
    def do_not_fail_with_teardown(self):
        return self._pytest_config.getvalue("do_not_fail_with_teardown")

    @property
    def sequential_execution(self):
        return self._pytest_config.getvalue("sequential_execution")

    @property
    def number_of_threads(self):
        return self._pytest_config.getvalue("number_of_threads")

    @property
    def probe_invoke_interval(self):
        return self._pytest_config.getvalue("probe_invoke_interval")

    @property
    def probe_wait_timeout(self):
        return self._pytest_config.getvalue("probe_wait_timeout")

    @property
    def bootstrap_wait_timeout(self):
        return self._pytest_config.getvalue("bootstrap_wait_timeout")

    @property
    def attached_tasks_wait_timeout(self):
        return self._pytest_config.getvalue("attached_tasks_wait_timeout")

    @property
    def completion_check_frequency(self):
        return self._pytest_config.getvalue("completion_check_frequency")

    @property
    def disable_at_teardown(self):
        return self._pytest_config.getvalue("disable_at_teardown")
