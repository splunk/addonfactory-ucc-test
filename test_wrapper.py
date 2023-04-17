from __future__ import print_function
import time
import os
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

def get_from_environment_variable(environment_variable: str) -> str:
    if environment_variable not in os.environ:
        print(f"{environment_variable} environment variable not set")
        exit(1)
    return os.environ[environment_variable]

configuration = swagger_client.Configuration()
configuration.host = configuration.host.replace('{domain}','localhost')
configuration.host = configuration.host.replace('{port}','8089')

configuration.verify_ssl = False
configuration.username = 'admin'
configuration.password = get_from_environment_variable("MODINPUT_TEST_SPLUNK_PASSWORD")

api_instance = swagger_client.DefaultApi(swagger_client.ApiClient(configuration))

output_mode = 'json'

instruction = '''
Open \\tmp\\restapi_client\\README.md to see all methods and how to use them.

To create modinput tests you will be interested in following methods:
1. api_instance.[TA_name]_settings_logging_post -   to set logging level
2. api_instance.[TA_name]_[configuration_tabs_name]_post -   to create specific configuration
3. api_instance.[TA_name]_[inputs_services_name]_post -   to create specific input
If you want to delete your configuration after tests, you will be interested in api_instance.[TA_name]_[configuration_tabs_name,inputs_services_name]_name_delete methods as well.

Edit test_wrapper.py to check code sample and write your code.
'''

#   once you starting yourt customisation, comment following print and exit so it does not confuse you
print(instruction)
exit(0)

#   BE AWARE
#   Following code sample is just an example
#   Write your own logic, that reflects your needs

# you may want to have debug information
try:
    api_response = api_instance.splunk_ta_jira_cloud_settings_logging_post(loglevel='DEBUG', output_mode=output_mode)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DefaultApi->splunk_ta_jira_cloud_settings_logging_post: %s\n" % e)

# you may want to store some values that shouldn't be publicly known as environment variables
domain_name = get_from_environment_variable("MODINPUT_TEST_JIRA_DOMAIN")
token_username = get_from_environment_variable("MODINPUT_TEST_JIRA_TOKEN_USERNAME")
token_value = get_from_environment_variable("MODINPUT_TEST_JIRA_TOKEN_VALUE")

# you may want to suffix configuration to distinguish execution cases
def get_timestamp():
    import time
    import datetime
    return datetime.datetime.fromtimestamp(time.time()).strftime('%Y%m%d%H%M%S')
test_suffix = get_timestamp()

token_name = f'tkn_{test_suffix}'
input_name = f'in_{test_suffix}'

# there is of course space for "standard" values
input_from = '2022-01-01T00:00:00'
input_interval = '60'
input_index = 'default'

# create configuration
try:
    api_response = api_instance.splunk_ta_jira_cloud_domain_post(name=domain_name, output_mode=output_mode)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DefaultApi->splunk_ta_jira_cloud_domain_post: %s\n" % e)

try:
    api_response = api_instance.splunk_ta_jira_cloud_api_token_post(domain=domain_name, name=token_name, username=token_username, token=token_value, output_mode=output_mode)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DefaultApi->splunk_ta_jira_cloud_api_token_name_post: %s\n" % e)

try:
    api_response = api_instance.splunk_ta_jira_cloud_jira_cloud_input_post(api_token=token_name, name=input_name, _from=input_from, interval=input_interval, index=input_index, output_mode=output_mode)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DefaultApi->splunk_ta_jira_cloud_jira_cloud_input_post: %s\n" % e)

# some tests here once configuration is ready
# ...

# tear down configuration when tests are done and you don't need the configuration anymore
try:
    api_response = api_instance.splunk_ta_jira_cloud_jira_cloud_input_name_delete(input_name, output_mode=output_mode)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DefaultApi->splunk_ta_jira_cloud_jira_cloud_input_name_delete: %s\n" % e)

try:
    api_response = api_instance.splunk_ta_jira_cloud_api_token_name_delete(token_name, output_mode=output_mode)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DefaultApi->splunk_ta_jira_cloud_api_token_name_delete: %s\n" % e)

try:
    api_response = api_instance.splunk_ta_jira_cloud_domain_name_delete(domain_name, output_mode=output_mode)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DefaultApi->splunk_ta_jira_cloud_domain_name_delete: %s\n" % e)