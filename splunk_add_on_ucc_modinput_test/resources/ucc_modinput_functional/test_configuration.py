import pytest  # noqa F401
from splunk_add_on_ucc_modinput_test.functional.decorators import (
    bootstrap,
    forge,
    forges,
)
from tests.ucc_modinput_functional import defaults
from tests.ucc_modinput_functional.splunk.forges import (
    ta_logging,
    account,
    another_account,
    another_account_index,
)


@bootstrap(
    forge(ta_logging),  # each forge will be executed just once,
    # no matter how many times appears in tests
)
def test_ta_logging(splunk_client):
    assert splunk_client.get_ta_log_level() == defaults.TA_LOG_LEVEL_FOR_TESTS


@bootstrap(
    forge(
        ta_logging
    ),  # sequence matters - ta_logging will be executed before accounts
    forges(  # there is parallel execution within forges
        forge(account),
        forge(another_account),
    ),
)
def test_accounts(
    splunk_client,
    # vendor_client,    # you may want to refer to it in most real-life cases
    account_config_name,
    another_account_config_name,
):
    actual_account = splunk_client.get_account(name=account_config_name)
    assert actual_account is not None
    assert actual_account.name == account_config_name
    assert actual_account.content.api_key == defaults.ENCRYPTED_VALUE

    actual_another_account = splunk_client.get_account(
        name=another_account_config_name
    )
    assert actual_another_account is not None
    assert actual_another_account.name == another_account_config_name
    assert actual_another_account.content.api_key == defaults.ENCRYPTED_VALUE


@bootstrap(
    forge(ta_logging),
    forges(
        forge(another_account_index),
        # the test framework creates session specific index that can be used
        # if more indexes are needed, they can be created as well
    ),
)
def test_indexes(splunk_client, another_account_index_name):
    splk_config = splunk_client.splunk_configuration
    actual_index = splk_config.get_index(
        another_account_index_name, client_service=splk_config.service
    )
    assert actual_index is not None
    assert actual_index.name == another_account_index_name
