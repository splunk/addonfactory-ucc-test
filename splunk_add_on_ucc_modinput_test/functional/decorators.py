from splunk_add_on_ucc_modinput_test.functional.constants import ForgeScope
from splunk_add_on_ucc_modinput_test.functional.manager import (
    dependency_manager,
)


def bootstrap(forge_fn, *, probe=None, scope=ForgeScope.SESSION, **kwargs):
    def bootstrap_dec(fn, *, act_as_decorator=True):
        if act_as_decorator:
            forge_descriptors = [(forge_fn, probe, scope, kwargs)]
            dependency_manager.bind(
                fn, scope, forge_descriptors, is_bootstrap=True
            )
            return fn

        return (forge_fn, probe, scope, kwargs)

    return bootstrap_dec


def bootstraps(*forge_list, scope=ForgeScope.SESSION):
    def bootstraps_dec(fn):
        forge_descriptors = []
        for frg in forge_list:
            assert frg.__name__ in ("bootstrap_dec", "forge_dec")
            forge_descriptors.append(frg(fn, act_as_decorator=False))
        dependency_manager.bind(
            fn, scope, forge_descriptors, is_bootstrap=True
        )
        return fn

    return bootstraps_dec


def forge(forge_fn, *, probe=None, scope=ForgeScope.SESSION, **kwargs):
    def forge_dec(fn, *, act_as_decorator=True):
        if act_as_decorator:
            forge_descriptors = [(forge_fn, probe, scope, kwargs)]
            dependency_manager.bind(
                fn, scope, forge_descriptors, is_bootstrap=False
            )
            return fn

        return (forge_fn, probe, scope, kwargs)

    return forge_dec


def forges(*forge_list, scope=ForgeScope.SESSION):
    def forges_dec(fn):
        forge_descriptors = []
        for frg in forge_list:
            assert frg.__name__ in ("forge_dec")
            forge_descriptors.append(frg(fn, act_as_decorator=False))
        dependency_manager.bind(
            fn, scope, forge_descriptors, is_bootstrap=False
        )
        return fn

    return forges_dec


def register_vendor_class(cls):
    dependency_manager.set_vendor_client_class(cls)
    return cls


def register_splunk_class(cls):
    dependency_manager.set_splunk_client_class(cls)
    return cls
