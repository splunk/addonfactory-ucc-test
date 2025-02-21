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
