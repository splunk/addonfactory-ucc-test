from typing import Dict
from splunk_add_on_ucc_modinput_test.common.utils import logger
from splunk_add_on_ucc_modinput_test.functional.decorators import (
    bootstrap,
    forge,
)
from tests.functional.common import SplunkClient, VendorClient


def forge1(
    splunk_client: SplunkClient,
    test_id: str,
    session_id: str,
    explicit_argument: int,
) -> Dict[str, object]:
    splunk_client.method(test_id)
    logger.info(f"forge1 test_id={test_id}")
    logger.info(f"forge1 session_id={session_id}")
    logger.info(f"forge1 explicit_argument={explicit_argument}")

    return dict(
        forge1_explicit_argument=explicit_argument,
        forge1_session_id=session_id,
        forge1_test_id=test_id,
    )


def forge2(
    vendor_client: VendorClient,
    test_id: str,
    session_id: str,
    explicit_argument: int,
) -> Dict[str, object]:
    vendor_client.method(test_id)
    logger.info(f"forge2 test_id={test_id}")
    logger.info(f"forge2 session_id={session_id}")
    logger.info(f"forge2 explicit_argument={explicit_argument}")

    return dict(
        forge2_explicit_argument=explicit_argument,
        forge2_session_id=session_id,
        forge2_test_id=test_id,
    )


@bootstrap(
    forge(forge1, explicit_argument=1),  # type: ignore
    forge(forge2, explicit_argument=2),
)
def test_arguments(
    splunk_client: SplunkClient,
    vendor_client: VendorClient,
    test_id: str,
    forge1_test_id: str,
    forge2_test_id: str,
    session_id: str,
    forge1_session_id,
    forge2_session_id,
    forge1_explicit_argument: int,
    forge2_explicit_argument: int,
) -> None:
    logger.info("test_arguments execution")
    assert splunk_client is not None
    assert vendor_client is not None
    assert forge1_test_id == test_id and forge2_test_id == test_id
    assert forge1_session_id == session_id and forge2_session_id == session_id
    assert forge1_explicit_argument == 1
    assert forge2_explicit_argument == 2
