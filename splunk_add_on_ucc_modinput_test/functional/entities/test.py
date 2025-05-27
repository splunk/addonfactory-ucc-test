#
# Copyright 2025 Splunk Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from copy import deepcopy
from typing import Any, Dict, Optional, Set
from splunk_add_on_ucc_modinput_test.functional import logger
from splunk_add_on_ucc_modinput_test.functional.constants import BuiltInArg
from splunk_add_on_ucc_modinput_test.functional.entities.executable import (
    ExecutableBase,
)
from splunk_add_on_ucc_modinput_test.functional.common.identifier_factory import (
    create_identifier,
    IdentifierType,
)
from splunk_add_on_ucc_modinput_test.typing import (
    ExecutableKeyType,
    TestFnType,
)


class FrameworkTest(ExecutableBase):
    def __init__(
        self,
        function: TestFnType,
        altered_name: Optional[str] = None,
    ) -> None:
        super().__init__(function)
        self.forges: Set[ExecutableKeyType] = set()
        self._is_executed: bool = False
        self._artifacts: Dict[str, Any] = {}
        if altered_name:
            self._fn_name = altered_name
        self._test_id = self.generate_test_id()

    @staticmethod
    def generate_test_id() -> str:
        return create_identifier(
            id_type=IdentifierType.ALPHA, in_uppercase=True
        )

    @property
    def test_id(self) -> str:
        return self._test_id

    @property
    def is_executed(self) -> bool:
        return self._is_executed

    @property
    def artifacts(self) -> Dict[str, Any]:
        return self._artifacts

    @property
    def name(self) -> str:
        return self.key[1]

    @property
    def path(self) -> str:
        return self.source_file

    @property
    def full_path(self) -> str:
        return "::".join(self.key)

    @property
    def original_full_path(self) -> str:
        return "::".join(self.original_key)

    def update_artifacts(self, artifacts: Dict[str, Any]) -> None:
        assert isinstance(artifacts, dict)
        self._artifacts.update(artifacts)

    def mark_executed(self) -> None:
        logger.debug(f"TEST: mark_executed {self}")
        self._is_executed = True

    def link_forge(self, forge_key: ExecutableKeyType) -> None:
        assert (
            forge_key not in self.forges
        ), "Attempt to assign the same forge multiply times or duplicated test name"
        self.forges.add(forge_key)

    def __repr__(self) -> str:
        return f"<Test {'::'.join(self.key)}>"

    @property
    def builtin_args(self) -> Dict[str, str]:
        return {BuiltInArg.TEST_ID.value: self.test_id}

    @property
    def artifacts_copy(self) -> Dict[str, Any]:
        try:
            # make a copy of artifacts if possible
            return deepcopy(self._artifacts)
        except TypeError:
            # copy is not possible, get artifacts by reference
            logger.warning(
                f"deepcopy of test artifacts is not possible, returning them by reference.\n\test:{self.key}\n\ttest artifacts: {self._artifacts}"
            )
            return self._artifacts

    def collect_required_kwargs(
        self, global_builtin_args: Dict[str, str]
    ) -> Dict[str, Any]:
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
