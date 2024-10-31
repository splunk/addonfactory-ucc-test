from splunk_add_on_ucc_modinput_test.functional.vendor.configuration import VendorConfigurationBase
class VendorClientBase:
    def __init__(self, vendor_configuration: VendorConfigurationBase):
        self._vendor_configuration = vendor_configuration

    @property
    def vendor_configuration(self):
        return self._vendor_configuration