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
from types import ModuleType
from typing import Any, Union, Tuple, Callable, Type
from splunk_add_on_ucc_modinput_test.common import ta_base
from splunk_add_on_ucc_modinput_test.functional import logger
from splunk_add_on_ucc_modinput_test.functional.manager import (
    dependency_manager,
    forge,
    forges,
)
from splunk_add_on_ucc_modinput_test.functional.splunk import (
    SplunkClientBase,
    SplunkConfigurationBase,
)
from splunk_add_on_ucc_modinput_test.functional.vendor import (
    VendorClientBase,
    VendorConfigurationBase,
)

from .constants import BuiltInArg


def bind(
    fn: Callable[..., Any],
    forges: Tuple[Union[forge, forges], ...],
    is_bootstrap: bool,
) -> None:
    for item in forges:
        scope = item.scope
        step_forges = (
            [item] if isinstance(item, forge) else list(item.forge_list)
        )
        dependency_manager.bind(fn, scope, step_forges, is_bootstrap)


def bootstrap(*forges: Union[forge, forges]) -> Callable[..., Any]:
    def bootstrap_dec(fn: Callable[..., Any]) -> Callable[..., Any]:
        bind(fn, forges, is_bootstrap=True)
        return fn

    return bootstrap_dec


def attach(*forges: Union[forge, forges]) -> Callable[..., Any]:
    def attach_dec(fn: Callable[..., Any]) -> Callable[..., Any]:
        bind(fn, forges, is_bootstrap=False)
        return fn

    return attach_dec


def define_vendor_client_argument(
    vendor_client_class: Type[VendorClientBase],
    vendor_class_argument_name: str = BuiltInArg.VENDOR_CLIENT.value,
) -> Callable[..., Any]:
    logger.debug(
        "attach_vendor_client_config vendor_client_class: "
        f"{vendor_client_class} with vendor_class_argument_name "
        + vendor_class_argument_name
    )

    def register_vendor_class_decorator(
        vendor_configuration_class: Type[VendorConfigurationBase],
    ) -> Type[VendorConfigurationBase]:
        dependency_manager.set_vendor_client_class(
            vendor_configuration_class,
            vendor_client_class,
            vendor_class_argument_name,
        )
        return vendor_configuration_class

    return register_vendor_class_decorator


def register_vendor_class(
    vendor_configuration_class: Type[
        VendorConfigurationBase
    ] = VendorConfigurationBase,
) -> Callable[..., Any]:
    logger.debug(f"register_vendor_class {vendor_configuration_class}")

    def register_vendor_class_decorator(
        vendor_client_class: Type[VendorClientBase],
    ) -> Type[VendorClientBase]:
        dependency_manager.set_vendor_client_class(
            vendor_configuration_class,
            vendor_client_class,
            BuiltInArg.VENDOR_CLIENT.value,
        )
        return vendor_client_class

    return register_vendor_class_decorator


def define_splunk_client_argument(
    swagger_client: ModuleType,
    splunk_client_class: Type[SplunkClientBase],
    splunk_class_argument_name: str = BuiltInArg.SPLUNK_CLIENT.value,
) -> Callable[..., Any]:
    logger.debug(
        "attach_splunk_client_config splunk_client_class: "
        f"{splunk_client_class} with "
        f"splunk_class_argument_name {splunk_class_argument_name}"
    )

    def _bind_swagger_client(self: SplunkClientBase) -> None:
        self.ta_service = ta_base.ConfigurationBase(
            swagger_client=swagger_client,
            splunk_configuration=self._splunk_configuration,
        )

    def register_splunk_class_decorator(
        splunk_configuration_class: Type[SplunkConfigurationBase],
    ) -> Type[SplunkConfigurationBase]:
        splunk_client_class._bind_swagger_client = _bind_swagger_client
        dependency_manager.set_splunk_client_class(
            splunk_configuration_class,
            splunk_client_class,
            splunk_class_argument_name,
        )
        return splunk_configuration_class

    return register_splunk_class_decorator


def register_splunk_class(
    swagger_client: ModuleType,
    splunk_configuration_class: Type[
        SplunkConfigurationBase
    ] = SplunkConfigurationBase,
) -> Callable[..., Any]:
    logger.debug(
        f"register_splunk_class swagger_client:{swagger_client} with "
        f"configuration {splunk_configuration_class}"
    )

    def _bind_swagger_client(self: SplunkClientBase) -> None:
        self.ta_service = ta_base.ConfigurationBase(
            swagger_client=swagger_client,
            splunk_configuration=self._splunk_configuration,
        )

    def register_splunk_class_decorator(
        splunk_client_class: Type[SplunkClientBase],
    ) -> Type[SplunkClientBase]:
        splunk_client_class._bind_swagger_client = _bind_swagger_client
        dependency_manager.set_splunk_client_class(
            splunk_configuration_class,
            splunk_client_class,
            BuiltInArg.SPLUNK_CLIENT.value,
        )
        return splunk_client_class

    return register_splunk_class_decorator
