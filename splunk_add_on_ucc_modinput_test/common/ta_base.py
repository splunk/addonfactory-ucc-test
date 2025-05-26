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
from typing import Dict, List
from types import ModuleType
from splunk_add_on_ucc_modinput_test.common import utils
from splunk_add_on_ucc_modinput_test.common.splunk_instance import (
    Configuration as SplunkConfiguration,
)


class InputConfigurationBase:
    def __init__(self, *, name_prefix: str, interval: int = 60):
        self._name = f"{name_prefix}{utils.Common().sufix}"
        self._interval = interval
        self._index = SplunkConfiguration().dedicated_index.name

    @property
    def name(self) -> str:
        return self._name

    @property
    def interval(self) -> int:
        return self._interval

    @property
    def index(self) -> str:
        return self._index


class ConfigurationBase:
    def __init__(
        self,
        *,
        swagger_client: ModuleType,
        splunk_configuration: SplunkConfiguration,
    ):
        self.splunk_configuration = splunk_configuration

        configuration = swagger_client.Configuration()
        configuration.host = configuration.host.replace(
            "{domain}", self.splunk_configuration.host
        )
        configuration.host = configuration.host.replace(
            "{port}", self.splunk_configuration.port
        )

        configuration.verify_ssl = False
        configuration.username = self.splunk_configuration.username
        configuration.password = self.splunk_configuration.password

        self._api_instance = swagger_client.DefaultApi(
            swagger_client.ApiClient(configuration)
        )
        self._inputs: Dict[str, InputConfigurationBase] = {}

        def api_instance(self) -> swagger_client.api.default_api.DefaultApi:  # type: ignore # noqa: E501
            return self._api_instance

        ConfigurationBase.api_instance = property(api_instance)  # type: ignore

    @property
    def dedicated_index_name(self) -> str:
        return self.splunk_configuration.dedicated_index.name

    def add_input_configuration(
        self, input_configuration: InputConfigurationBase
    ) -> None:
        self._inputs[input_configuration.name] = input_configuration

    def get_all_inputs(self) -> List[InputConfigurationBase]:
        return [i for i in self._inputs.values()]

    def get_input_configuration(
        self, name_prefix: str
    ) -> InputConfigurationBase:
        return self._inputs[f"{name_prefix}{utils.Common().sufix}"]
