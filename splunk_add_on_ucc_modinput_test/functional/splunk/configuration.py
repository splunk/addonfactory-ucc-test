from splunk_add_on_ucc_modinput_test.common.splunk_instance import (
    Configuration,
)
from splunk_add_on_ucc_modinput_test.functional.common.pytest_config_adapter import (  # noqa E501
    PytestConfigAdapter,
)


class SplunkConfigurationBase(Configuration, PytestConfigAdapter):
    def __init__(self, pytest_config):
        Configuration.__init__(self)
        PytestConfigAdapter.__init__(self, pytest_config)
        self.customize_configuration()

    def customize_configuration(self):
        pass
