import time
import json
import requests
from requests.auth import HTTPBasicAuth
from splunk_add_on_ucc_modinput_test.common import utils


class Configuration:
    def __init__(self):
        self._domain = utils.get_from_environment_variable(
            "MODINPUT_TEST_JIRACLOUD_DOMAIN"
        )
        self._token_username = utils.get_from_environment_variable(
            "MODINPUT_TEST_JIRACLOUD_TOKEN_USERNAME"
        )
        self._token_value = utils.get_from_environment_variable(
            "MODINPUT_TEST_JIRACLOUD_TOKEN_VALUE"
        )

    @property
    def domain(self):
        return self._domain

    @property
    def token_username(self):
        return self._token_username

    @property
    def token_value(self):
        return self._token_value


def group_create_and_delete(configuration: Configuration):
    _GROUP_NAME = f"g_{utils.Common().sufix}"

    url = f"https://{configuration.domain}.atlassian.net/rest/api/2/group"

    auth = HTTPBasicAuth(configuration.token_username, configuration.token_value)
    headers = {"Accept": "application/json", "Content-Type": "application/json"}

    payload = json.dumps({"name": _GROUP_NAME})

    try:
        response = requests.request(
            "POST", url, data=payload, headers=headers, auth=auth
        )
    except Exception as e:
        msg = f"Error occured during Jira Cloud group {_GROUP_NAME} creation:\n{e}"
        utils.logger.error(msg)
        pytest.exit(1, msg=msg)
    response_json = json.loads(response.text)
    utils.logger.debug(
        json.dumps(response_json, sort_keys=True, indent=4, separators=(",", ": "))
    )
    groupId = response_json["groupId"]

    time.sleep(10)  # Jira Cloud needs a time to populate the change

    query = {"groupId": f"{groupId}"}
    try:
        response = requests.request("DELETE", url, params=query, auth=auth)
    except Exception as e:
        msg = f"Error occured during Jira Cloud group {_GROUP_NAME} deletion (groupId: {groupId}):\n{e}"
        utils.logger.error(msg)
        pytest.exit(1, msg=msg)
    utils.logger.debug(response.text)
