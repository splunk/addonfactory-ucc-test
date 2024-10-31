from splunk_add_on_ucc_modinput_test.functional.common.pytest_config_adapter import PytestConfigAdapter
class VendorConfigurationBase(PytestConfigAdapter):
    def __init__(self, pytest_config):
        super().__init__(pytest_config)
        self.customize_configuration()
        
    def customize_configuration(self):
        pass