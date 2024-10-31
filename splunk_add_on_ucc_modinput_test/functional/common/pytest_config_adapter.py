class PytestConfigAdapter:
    def __init__(self, pytest_config=None):
        self._pytest_config = pytest_config
    
    def link_pytest_config(self, pytest_config):
        self._pytest_config = pytest_config

    @property
    def pytest_config(self):
        return self._pytest_config
    
    @property
    def fail_with_teardown(self):
        return self._pytest_config.getvalue("fail_with_teardown")

    @property
    def sequential_execution(self):
        return self._pytest_config.getvalue("sequential_execution")

    @property
    def number_of_threads(self):
        return self._pytest_config.getvalue("number_of_threads")
