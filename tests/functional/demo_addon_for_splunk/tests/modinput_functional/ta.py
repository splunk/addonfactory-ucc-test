from splunk_add_on_ucc_modinput_test.common.splunk_instance import Configuration as SplunkConfiguration
from tests.modinput_functional.vendor_product import Configuration as VendorProductConfiguration
from splunk_add_on_ucc_modinput_test.common import utils
from splunk_add_on_ucc_modinput_test.common.ta_base import ConfigurationBase, InputConfigurationBase
from swagger_client.rest import ApiException

output_mode = "json"
pprint = utils.logger.debug
print = utils.logger.error

NAME = "demo_addon_for_splunk"

# create modinput type specific classes
# InputTypeAbcConfiguration and InputTypeXyzConfiguration are just examples
# and should be used as motivation for your code
# Remember to remove the example code once you are done with your customizations
class InputTypeEndpointConfiguration(InputConfigurationBase):
    # kwarguments (the one following *) are TA specific and should be a subject of customization
    # you may want to customize list of positional arguments (before *), if you want to customize default interval
    def __init__(
        self,
        name_prefix: str,
        *,
        endpoint_name: str,
        source_type: str,
    ):
        super().__init__(name_prefix=name_prefix)
        # kwarguments assignment is TA specific
        self.endpoint_name = endpoint_name
        self.source_type = source_type

#   do not modify the code below
class Configuration(ConfigurationBase):
    def __init__(
        self,
        *,
        splunk_configuration: SplunkConfiguration,
        vendor_product_configuration: VendorProductConfiguration,
    ):
        super().__init__(
            splunk_configuration=splunk_configuration,
            vendor_product_configuration=vendor_product_configuration,
        )
#   do not modify the code above
        self.source_type = "demo"
        self.endpoints = {
            f"endpoint1_{utils.Common().sufix}":self.vendor_product_configuration.endpoint1,
            f"endpoint2_{utils.Common().sufix}":self.vendor_product_configuration.endpoint2,
            f"endpoint3_{utils.Common().sufix}":self.vendor_product_configuration.endpoint3,
        }
#   add input configuration to inputs list
        for endpoint_name in self.endpoints:
            self.add_input_configuration(
                InputTypeEndpointConfiguration(
                    name_prefix=f"in{endpoint_name[len('endpoint'):-len(utils.Common().sufix)]}",
                    endpoint_name=endpoint_name,
                    source_type=self.source_type
                )
            )

#   BE AWARE
#   set_up and tear_down methods are required by the framework
    def set_up(self, api_instance):
        
        #   keep setting loglevel to DEBUG as a good practice
        try:
            api_response = api_instance.demo_addon_for_splunk_settings_logging_post(output_mode, loglevel="DEBUG")
            pprint(api_response)
        except ApiException as e:
            print("Exception when calling DefaultApi->demo_addon_for_splunk_settings_logging_post: %s\n" % e)
        # create vendor product specific configuration

        for endpoint_name, endpoint_uri in self.endpoints.items():
            try:
                api_response = api_instance.demo_addon_for_splunk_endpoint_post(output_mode, name=endpoint_name, uri=endpoint_uri)
                pprint(api_response)
            except ApiException as e:
                print("Exception when calling DefaultApi->demo_addon_for_splunk_endpoint_post: %s\n" % e)

        #   create all inputs
        for input_configuration in self.get_all_inputs():
            if isinstance(input_configuration, InputTypeEndpointConfiguration):
                try:
                    api_response = api_instance.demo_addon_for_splunk_demo_input_post(output_mode, name=input_configuration.name, interval=input_configuration.interval, endpoint=input_configuration.endpoint_name, sourcetype=input_configuration.source_type, index=input_configuration.index)
                    pprint(api_response)
                except ApiException as e:
                    print("Exception when calling DefaultApi->demo_addon_for_splunk_demo_input_post: %s\n" % e)

#   BE AWARE
#   set_up and tear_down methods are required by the framework
    def tear_down(self, api_instance):
        #   disable all inputs
        for input_configuration in self.get_all_inputs():
            if isinstance(input_configuration, InputTypeEndpointConfiguration):
                try:
                    api_response = api_instance.demo_addon_for_splunk_demo_input_name_post(output_mode, input_configuration.name, disabled=True)
                    pprint(api_response)
                except ApiException as e:
                    print("Exception when calling DefaultApi->demo_addon_for_splunk_demo_input_name_post: %s\n" % e)
