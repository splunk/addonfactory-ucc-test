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
from splunk_add_on_ucc_modinput_test.functional.vendor.configuration import (
    VendorConfigurationBase,
)


class VendorClientBase:
    def __init__(self, vendor_configuration: VendorConfigurationBase) -> None:
        self._vendor_configuration = vendor_configuration

    @property
    def vendor_configuration(self) -> VendorConfigurationBase:
        return self._vendor_configuration

    @property
    def config(
        self,
    ) -> VendorConfigurationBase:  # short alias for vendor_configuration
        return self._vendor_configuration
