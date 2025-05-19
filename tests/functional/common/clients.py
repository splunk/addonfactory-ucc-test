import time
import random

from splunk_add_on_ucc_modinput_test.common.utils import logger
from splunk_add_on_ucc_modinput_test.functional.decorators import (
    register_splunk_class,
    register_vendor_class,
)
from splunk_add_on_ucc_modinput_test.functional.splunk import (
    SplunkClientBase,
    SplunkConfigurationBase,
)

from splunk_add_on_ucc_modinput_test.functional.vendor import (
    VendorClientBase,
    VendorConfigurationBase,
)
from tests.functional.common import swagger_client


class SplunkConfiguration(SplunkConfigurationBase):
    def __new__(cls, *args, **kwargs):  # return type: ignore
        return object.__new__(cls)


@register_splunk_class(swagger_client, SplunkConfiguration)
class SplunkClient(SplunkClientBase):
    def __init__(*args, **kwargs):
        pass

    def method(self, id=None, *args, **kwargs):
        timeout = random.random()
        logger.info(f"{id}: Splunk client method start, timeout={timeout}")
        time.sleep(timeout)
        logger.info("Splunk client method complete")


class VendorConfiguration(VendorConfigurationBase):
    pass


@register_vendor_class(VendorConfiguration)
class VendorClient(VendorClientBase):
    def method(self, id=None, *args, **kwargs):
        timeout = 0.5 + random.random()
        logger.info(f"{id}: Vendor client method start, timeout={timeout}")
        time.sleep(timeout)
        logger.info(f"{id}: Vendor client method complete")
