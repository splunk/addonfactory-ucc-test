from types import ModuleType
from typing import Any, Union, Tuple, Callable
from splunk_add_on_ucc_modinput_test.common import ta_base
from splunk_add_on_ucc_modinput_test.functional.manager import (
    dependency_manager,
    forge,
    forges,
)


def bind(
    fn: Callable[..., Any],
    forges: Tuple[Union[forge, forges], ...],
    is_bootstrap: bool,
) -> None:
    for item in forges:
        if isinstance(item, forge):
            scope = item.scope
            step_forges = [item]
        else:
            scope = item.scope
            step_forges = item.forge_list

        dependency_manager.bind(fn, scope, step_forges, is_bootstrap)


def bootstrap(*forges: Tuple[Union[forge, forges], ...]) -> Callable[..., Any]:
    def bootstrap_dec(fn: Callable[..., Any]) -> Callable[..., Any]:
        bind(fn, forges, is_bootstrap=True)
        return fn

    return bootstrap_dec


def attach(*forges: Tuple[Union[forge, forges], ...]) -> Callable[..., Any]:
    def attach_dec(fn: Callable[..., Any]) -> Callable[..., Any]:
        bind(fn, forges, is_bootstrap=False)
        return fn

    return attach_dec


def register_vendor_class(cls):
    dependency_manager.set_vendor_client_class(cls)
    return cls


def register_splunk_class(swagger_client:ModuleType):
    def _bind_swager_client(self):
        self.ta_service = ta_base.ConfigurationBase(
            swagger_client = swagger_client,
            splunk_configuration=self._splunk_configuration,
        )


    def register_splunk_class_decorator(cls):    
        cls._bind_swager_client = _bind_swager_client
        dependency_manager.set_splunk_client_class(cls)
        return cls
    
    return register_splunk_class_decorator