import pytest
from unittest.mock import MagicMock, patch
from splunk_add_on_ucc_modinput_test.common.splunk_instance import (
    Configuration,
)


def test_validate_index_name_valid() -> None:
    Configuration._validate_index_name("valid_index-123")


def test_validate_index_name_invalid_character() -> None:
    invalid_names = ["index$", "index!", "index@", "index#"]
    for name in invalid_names:
        with pytest.raises(
            ValueError,
            match="Index name must consist of only numbers, "
            "lowercase letters, underscores, and hyphens.",
        ):
            Configuration._validate_index_name(name)


def test_validate_index_name_starts_with_invalid_character() -> None:
    invalid_names = ["-index", "_index"]
    with pytest.raises(
        ValueError,
        match="Index name cannot begin with an underscore or hyphen.",
    ):
        for name in invalid_names:
            Configuration._validate_index_name(name)


@pytest.mark.parametrize("response_status", [404, 500])
@patch(
    "splunk_add_on_ucc_modinput_test.common.splunk_instance.request.urlopen"
)
def test_get_index_from_classic_instance_none(mock_urlopen, response_status):
    mock_response = MagicMock()
    mock_response.status = response_status
    mock_urlopen.return_value.__enter__.return_value = mock_response

    mock_client = MagicMock()
    mock_client._host = "idm1.mock_acs.splunkcloud.com"
    mock_client._port = 8089
    mock_client._username = "mock_user"
    mock_client._password = "mock_password"
    cloud_index = Configuration.get_index_from_classic_instance(
        "test_index",
        mock_client,
        "mock_acs",
        "https://mock_server.com",
        "test_token",
    )

    assert cloud_index is None
    mock_urlopen.assert_called_once()
