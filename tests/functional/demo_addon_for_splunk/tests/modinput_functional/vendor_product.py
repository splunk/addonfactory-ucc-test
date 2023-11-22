from splunk_add_on_ucc_modinput_test.common import utils

#   BE AWARE
#   the file content is extremely vendor product specific
#   to be consistent with framework, you just need to keep Configuration class
#   it is also adviced to have unique events creation in dedicated functions


class Configuration:
    def __init__(self):
        self._endpoint1 = utils.get_from_environment_variable(
            "MODINPUT_TEST_DEMO_ENDPOINT1"
        )
        self._endpoint2 = utils.get_from_environment_variable(
            "MODINPUT_TEST_DEMO_ENDPOINT2"
        )
        self._endpoint3 = utils.get_from_environment_variable(
            "MODINPUT_TEST_DEMO_ENDPOINT3"
        )

    @property
    def endpoint1(self):
        return self._endpoint1

    @property
    def endpoint2(self):
        return self._endpoint2

    @property
    def endpoint3(self):
        return self._endpoint3


def patch_endpoint(*, url: str, message: str = None) -> str:
    import requests

    request_json = {"message": message} if message else {}
    response = requests.patch(url, json=request_json)
    return (
        "POST Request Successful"
        if response.ok
        else f"POST Request Failed with status code: {response.status_code}"
    )


def patch_endpoint1(configuration: Configuration, message: str = None) -> str:
    return patch_endpoint(url=configuration.endpoint1, message=message)


def patch_endpoint2(configuration: Configuration, message: str = None) -> str:
    return patch_endpoint(url=configuration.endpoint2, message=message)


def patch_endpoint3(configuration: Configuration, message: str = None) -> str:
    return patch_endpoint(url=configuration.endpoint3, message=message)
