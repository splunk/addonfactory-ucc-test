import time
import random
from splunk_add_on_ucc_modinput_test.functional import logger
from splunk_add_on_ucc_modinput_test.functional.constants import (
    BuiltInArg,
)
from splunk_add_on_ucc_modinput_test.functional.entities.executable import (
    ExecutableBase,
)


class FrameworkTest(ExecutableBase):
    def __init__(self, function, altered_name=None):
        super().__init__(function)
        self.forges = set()
        self._is_executed = False
        self._artifacts = {}
        if altered_name:
            self._fn_name = altered_name
        self._test_id = self.generate_test_id()

    @staticmethod
    def generate_test_id():
        time_based = int(time.time()*10**5)%10**10
        return hex(time_based*10**3 + random.randint(0, 10**3))[2:]

    @property
    def test_id(self):
        return self._test_id

    @property
    def is_executed(self):
        return self._is_executed

    @property
    def artifacts(self):
        return self._artifacts

    @property
    def name(self):
        return self.key[1]

    @property
    def path(self):
        return self.source_file

    @property
    def full_path(self):
        return "::".join(self.key)

    def update_artifacts(self, artifacts):
        assert isinstance(artifacts, dict)
        return self._artifacts.update(artifacts)

    def mark_executed(self):
        logger.debug(f"TEST: mark_executed {self}")
        self._is_executed = True

    def link_forge(self, forge_key):
        assert forge_key not in self.forges
        self.forges.add(forge_key)

    def __repr__(self):
        return f"<Test {'::'.join(self.key)}>"

    def collect_required_kwargs(self, session_id):
        kwargs = {
            k: v
            for k, v in self._artifacts.items()
            if k in self._required_args
        }
        if (BuiltInArg.TEST_ID.value in self._required_args):
            kwargs[BuiltInArg.TEST_ID.value] = self._test_id
            
        if (BuiltInArg.SESSION_ID.value in self._required_args):
            kwargs[BuiltInArg.SESSION_ID.value] = session_id

        logger.debug(
            f"Finish collect_required_kwargs for test {self.key}: kwargs={kwargs}"
        )
        return kwargs
