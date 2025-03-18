
import pytest
from pathlib import Path

from splunk_add_on_ucc_modinput_test.common import bootstrap

def test_load_readme_examples():
    examples =  bootstrap.load_readme_examples(swagger_client_readme_md=Path("tests/unit/resources/README.md"))

    splunk_ta_example_account_get = """api_instance = swagger_client.DefaultApi(swagger_client.ApiClient(configuration))
output_mode = 'json' # str | Output mode (default to json)

try:
    api_response = api_instance.splunk_ta_example_account_get(output_mode)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DefaultApi->splunk_ta_example_account_get: %s\\n" % e)
# Configure HTTP basic authorization: BasicAuth
configuration = swagger_client.Configuration()
configuration.username = 'YOUR_USERNAME'
configuration.password = 'YOUR_PASSWORD'"""

    assert splunk_ta_example_account_get in examples