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
from splunk_add_on_ucc_modinput_test.functional.common.pytest_config_adapter import (  # noqa E501
    PytestConfigAdapter,
)
from pytest import Config


class VendorConfigurationBase(PytestConfigAdapter):
    def __init__(self, pytest_config: Config) -> None:
        super().__init__(pytest_config)
        self.customize_configuration()

    def customize_configuration(self) -> None:
        pass
