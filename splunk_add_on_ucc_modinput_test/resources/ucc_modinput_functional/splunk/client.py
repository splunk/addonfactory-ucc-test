from splunk_add_on_ucc_modinput_test.functional.decorators import (
    register_splunk_class,
)
from splunk_add_on_ucc_modinput_test.functional.splunk.client import (
    SplunkClientBase,
)

from splunk_add_on_ucc_modinput_test.common import utils
from splunk_add_on_ucc_modinput_test.common import splunk_instance

import swagger_client

from swagger_client.rest import ApiException
from tests.ucc_modinput_functional import defaults

pprint = utils.logger.debug
print = utils.logger.error
output_mode = "json"


@register_splunk_class(swagger_client)
class SplunkClient(SplunkClientBase):
    NAME = "Splunk_TA_salesforce"

    def search(self, searchquery):
        return splunk_instance.search(
            service=self.splunk, searchquery=searchquery
        )

    def get_ta_log_level(self):
        # find relevant part in swagger_client README.md
        # copy and paste here
        try:
            # api_response = api_instance.splunk_ta_example_settings_logging_get(output_mode) # noqa: E501
            # replace "api_instance." with "self.ta_api."
            api_response = self.ta_api.splunk_ta_example_settings_logging_get(
                output_mode
            )
            pprint(api_response)
        except ApiException as e:
            print(
                "Exception when calling DefaultApi->\
                    splunk_ta_example_settings_logging_get: %s\n"
                % e
            )
        # if you want to return any value, add return section
        else:
            return api_response.entry[0].content.loglevel

    def set_ta_log_level(
        self, loglevel: str = defaults.TA_LOG_LEVEL_FOR_TESTS
    ):
        pprint(f"Configuring TA log level to {loglevel}")
        try:
            api_response = self.ta_api.splunk_ta_example_settings_logging_post(
                output_mode, loglevel=loglevel
            )
            pprint(api_response)
        except ApiException as e:
            print(
                "Exception when calling DefaultApi->\
                    splunk_ta_example_settings_logging_post: %s\n"
                % e
            )

    def create_account(
        self,
        *,
        name: str,
        api_key: str,
    ):
        try:
            api_response = self.ta_api.splunk_ta_example_account_post(
                output_mode, name=name, api_key=api_key
            )
            pprint(api_response)
        except ApiException as e:
            print(
                "Exception when calling DefaultApi->\
                    splunk_ta_example_account_post: %s\n"
                % e
            )

    def get_account(
        self,
        *,
        name: str,
    ):
        try:
            api_response = self.ta_api.splunk_ta_example_account_name_get(
                name, output_mode
            )
            pprint(api_response)
        except ApiException as e:
            print(
                "Exception when calling DefaultApi->\
                    splunk_ta_example_account_name_get: %s\n"
                % e
            )
        else:
            return api_response.entry[0]

    def create_input(
        self,
        *,
        name: str,
        interval: str,
        index: str,
        account: str,
    ):
        try:
            # api_response = self.ta_api.splunk_ta_example_example_post(output_mode, name=name, interval=interval, index=index, account=account, fetch_from=fetch_from, start_from=start_from) # noqa: E501
            # fetch_from and start_from were created to show UCC options
            # by UI side and are not used by server side any way,
            # that's why we are skipping them here
            api_response = self.ta_api.splunk_ta_example_example_post(
                output_mode,
                name=name,
                interval=interval,
                index=index,
                account=account,
            )
            pprint(api_response)
        except ApiException as e:
            print(
                "Exception when calling DefaultApi->\
                    splunk_ta_example_example_post: %s\n"
                % e
            )

    def disable_input(self, *, name: str):
        try:
            api_response = self.ta_api.splunk_ta_example_example_name_post(
                output_mode, name, disabled=True
            )
            pprint(api_response)
        except ApiException as e:
            print(
                "Exception when calling DefaultApi->\
                    splunk_ta_example_example_name_post: %s\n"
                % e
            )
