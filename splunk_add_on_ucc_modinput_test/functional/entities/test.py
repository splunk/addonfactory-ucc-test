from copy import deepcopy
from splunk_add_on_ucc_modinput_test.functional import logger
from splunk_add_on_ucc_modinput_test.functional.constants import BuiltInArg
from splunk_add_on_ucc_modinput_test.functional.entities.executable import (
    ExecutableBase,
)
from splunk_add_on_ucc_modinput_test.functional.common.identifier_factory import (
    create_identifier,
    IdentifierType,
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
        return create_identifier(
            id_type=IdentifierType.ALPHA, in_uppercase=True
        )

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

    @property
    def original_full_path(self):
        return "::".join(self.original_key)

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

    @property
    def builtin_args(self):
        return {BuiltInArg.TEST_ID.value: self.test_id}

    @property
    def artifacts_copy(self):
        return deepcopy(self._artifacts)

    def collect_required_kwargs(self, global_builtin_args):
        all_args = self.artifacts_copy
        all_args.update(self.builtin_args)
        all_args.update(global_builtin_args)
        required_args = {
            k: v for k, v in all_args.items() if k in self._required_args
        }
        logger.debug(
            f"Finish collect_required_kwargs for test {self.key}: kwargs={required_args}"
        )
        return required_args
