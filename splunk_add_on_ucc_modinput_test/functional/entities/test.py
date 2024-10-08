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

    @property
    def is_executed(self):
        return self._is_executed

    @property
    def artifacts(self):
        return self._artifacts

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

    def collect_required_kwargs(self, splunk_client=None, vendor_client=None):
        kwargs = {
            k: v
            for k, v in self._artifacts.items()
            if k in self._required_args
        }
        if (
            splunk_client
            and BuiltInArg.SPLUNK_CLIENT.value in self._required_args
        ):
            kwargs[BuiltInArg.SPLUNK_CLIENT.value] = splunk_client
        if (
            vendor_client
            and BuiltInArg.VENDOR_CLIENT.value in self._required_args
        ):
            kwargs[BuiltInArg.VENDOR_CLIENT.value] = vendor_client
        logger.debug(
            f"Finish collect_required_kwargs for test {self.key}: kwargs={kwargs}"
        )
        return kwargs
