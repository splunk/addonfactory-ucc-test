from typing import Dict
from splunk_add_on_ucc_modinput_test.functional.decorators import (
    bootstrap,
    forge,
)
from splunk_add_on_ucc_modinput_test.typing import ProbeGenType
from tests.functional.common import SplunkClient, VendorClient
import logging

logger = logging.getLogger("ucc-modinput-test")
probe_fn_external_counter = 3


def probe_fn() -> bool:
    global probe_fn_external_counter
    if probe_fn_external_counter > 0:
        probe_fn_external_counter -= 1
    res = probe_fn_external_counter == 0
    logger.debug(
        "probe_fn probe_fn_external_counter="
        f"{probe_fn_external_counter}, returns {res}"
    )
    return res


def probe_gen(probe_fn: bool) -> ProbeGenType:
    logger.debug("probe_gen fail, wait 0.2")
    yield 0.2
    logger.debug("probe_gen fail, wait 0.2")
    yield 0.5

    res = not probe_fn
    logger.debug("probe_gen exit with {res}")
    return res


def forge1(
    splunk_client: SplunkClient,
    test_id: str,
    session_id: str,
    explicit_argument: int,
) -> Dict[str, object]:
    splunk_client.method(test_id)
    return dict(
        forge1_splunk_client=splunk_client,
        forge1_explicit_argument=explicit_argument,
        forge1_session_id=session_id,
        forge1_test_id=test_id,
    )


def forge2(
    vendor_client: VendorClient,
    test_id: str,
    session_id: str,
    explicit_argument: int,
    probe_fn: bool,
) -> Dict[str, object]:
    vendor_client.method(test_id)
    return dict(
        forge2_vendor_client=vendor_client,
        forge2_explicit_argument=explicit_argument,
        forge2_session_id=session_id,
        forge2_test_id=test_id,
        forge2_probe_fn=probe_fn,
    )


@bootstrap(
    forge(forge1, explicit_argument=1, probe=probe_fn),  # type: ignore
    forge(forge2, explicit_argument=2, probe=probe_gen),
)
def test_arguments(
    splunk_client: SplunkClient,
    forge1_splunk_client: SplunkClient,
    vendor_client: VendorClient,
    forge2_vendor_client: VendorClient,
    test_id: str,
    forge1_test_id: str,
    forge2_test_id: str,
    session_id: str,
    forge1_session_id,
    forge2_session_id,
    forge1_explicit_argument: int,
    forge2_explicit_argument: int,
    forge2_probe_fn: bool,
    probe_gen: bool,
    probe_fn: bool,
) -> None:
    logger.info("test_arguments execution")
    assert splunk_client is forge1_splunk_client
    assert vendor_client is forge2_vendor_client
    assert forge1_test_id == test_id and forge2_test_id == test_id
    assert forge1_session_id == session_id and forge2_session_id == session_id
    assert forge1_explicit_argument == 1
    assert forge2_explicit_argument == 2
    assert forge2_probe_fn == probe_fn
    assert probe_gen != probe_fn
