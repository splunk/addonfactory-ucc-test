from splunk_add_on_ucc_modinput_test.common.splunk_instance import Configuration as SplunkConfiguration
from tests.modinput_functional.vendor_product import Configuration as VendorProductConfiguration
from splunk_add_on_ucc_modinput_test.common import utils
from splunk_add_on_ucc_modinput_test.common.ta_base import ConfigurationBase, InputConfigurationBase
from swagger_client.rest import ApiException

output_mode = "json"
pprint = utils.logger.debug
print = utils.logger.error


class InputConfiguration(InputConfigurationBase):
    # kvarguments are TA specific
    def __init__(
        self,
        name_prefix: str,
        *,
        token_name: str,
        from_timestamp: str,
    ):
        super().__init__(name_prefix=name_prefix)
        # kvarguments assignment is TA specific
        self.token_name = token_name
        self.from_timestamp = from_timestamp


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

        self.token_name = f"tkn_{utils.Common().sufix}"
        #   variables that are defined in TA Configuration (as token) may be needed in setup and teardown operations
        #   so are assigned to Configuration object
        from_timestamp = utils.convert_to_utc(
            utils.Common().start_timestamp, format="%Y-%m-%dT%H:%M:%S"
        )
        #   while other are Inputs specific so stay private for __init__ method

        #   this input configuration does have a meaning
        #   for production scenario
        self.add_input_configuration(
            InputConfiguration(
                name_prefix="in_",
                token_name=self.token_name,
                from_timestamp=from_timestamp,
            )
        )
        #   this input configuration is created
        #   just to show support for many inputs
        self.add_input_configuration(
            InputConfiguration(
                name_prefix="fake_in_",
                token_name=self.token_name,
                from_timestamp=from_timestamp,
            )
        )

    def set_up(self, api_instance):
        #   keep setting loglevel to DEBUG as a good practice
        try:
            api_response = api_instance.splunk_ta_jira_cloud_settings_logging_post(
                output_mode=output_mode, loglevel="DEBUG"
            )
            pprint(api_response)
        except ApiException as e:
            print(
                "Exception when calling DefaultApi->splunk_ta_jira_cloud_settings_logging_post: %s\n"
                % e
            )

        # create vendor product specific configuration
        try:
            api_response = api_instance.splunk_ta_jira_cloud_domain_get(
                output_mode=output_mode
            )
            pprint(api_response)
        except ApiException as e:
            print(
                "Exception when calling DefaultApi->splunk_ta_jira_cloud_domain_get: %s\n"
                % e
            )
        try:
            api_response = api_instance.splunk_ta_jira_cloud_domain_post(
                output_mode=output_mode, name=self.vendor_product_configuration.domain
            )
            pprint(api_response)
        except ApiException as e:
            print(
                "Exception when calling DefaultApi->splunk_ta_jira_cloud_domain_post: %s\n"
                % e
            )

        try:
            api_response = api_instance.splunk_ta_jira_cloud_api_token_post(
                output_mode=output_mode,
                domain=self.vendor_product_configuration.domain,
                name=self.token_name,
                username=self.vendor_product_configuration.token_username,
                token=self.vendor_product_configuration.token_value,
            )
            pprint(api_response)
        except ApiException as e:
            print(
                "Exception when calling DefaultApi->splunk_ta_jira_cloud_api_token_name_post: %s\n"
                % e
            )

        #   create all inputs
        for input_configuration in self.get_all_inputs():
            try:
                api_response = api_instance.splunk_ta_jira_cloud_jira_cloud_input_post(
                    output_mode=output_mode,
                    api_token=input_configuration.token_name,
                    name=input_configuration.name,
                    _from=input_configuration.from_timestamp,
                    interval=input_configuration.interval,
                    index=input_configuration.index,
                )
                pprint(api_response)
            except ApiException as e:
                print(
                    "Exception when calling DefaultApi->splunk_ta_jira_cloud_jira_cloud_input_post: %s\n"
                    % e
                )

    def tear_down(self, api_instance):
        #   disable all inputs
        for input_configuration in self.get_all_inputs():
            try:
                api_response = (
                    api_instance.splunk_ta_jira_cloud_jira_cloud_input_name_post(
                        output_mode=output_mode,
                        name=input_configuration.name,
                        disabled=True,
                    )
                )
                pprint(api_response)
            except ApiException as e:
                print(
                    "Exception when calling DefaultApi->splunk_ta_jira_cloud_jira_cloud_input_name_post: %s\n"
                    % e
                )
