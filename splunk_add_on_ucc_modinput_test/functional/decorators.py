from splunk_add_on_ucc_modinput_test.functional import logger
from splunk_add_on_ucc_modinput_test.functional.constants import ForgeScope
from splunk_add_on_ucc_modinput_test.functional.manager import (
    dependency_manager,
)
from splunk_add_on_ucc_modinput_test.functional.splunk.client import (
    SplunkClientBase,
)
from splunk_add_on_ucc_modinput_test.functional.vendor.client import (
    VendorClientBase,
)


def forge(forge_fn, *, probe=None, scope=ForgeScope.SESSION, **kwargs):
    def forge_dec(fn, *, act_as_decorator=True):
        if act_as_decorator:
            forge_descriptors = [(forge_fn, probe, scope, kwargs)]
            dependency_manager.bind(fn, scope, forge_descriptors)
            return fn

        return (forge_fn, probe, scope, kwargs)

    return forge_dec


def forges(*forge_list, scope=ForgeScope.SESSION):
    def forges_dec(fn):
        forge_descriptors = [
            frg(fn, act_as_decorator=False) for frg in forge_list
        ]
        dependency_manager.bind(fn, scope, forge_descriptors)
        return fn

    return forges_dec


def register_vendor_class(cls):
    dependency_manager.set_vendor_client_class(cls)
    return cls


def register_splunk_class(cls):
    dependency_manager.set_splunk_client_class(cls)
    return cls
