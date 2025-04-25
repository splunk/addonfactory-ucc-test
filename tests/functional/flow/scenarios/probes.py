from typing import Dict
from splunk_add_on_ucc_modinput_test.common.utils import logger
from splunk_add_on_ucc_modinput_test.functional.decorators import (
    bootstrap,
    forge,
)
from tests.functional.common import VendorClient, SplunkClient
from splunk_add_on_ucc_modinput_test.typing import ProbeGenType


def probe1(test_id: str) -> ProbeGenType:
    for _ in range(2):
        logger.info(f"probe1 for test_id={test_id} is negative")
        yield 0.5
    logger.info(f"probe1 for test_id={test_id} has succeeded")
    return True


def probe2(test_id: str, probe1: bool) -> ProbeGenType:
    for _ in range(2):
        logger.info(f"probe2 for test_id={test_id} is negative")
        yield 0.5

    probe_status = "succeeded" if not probe1 else "failed"
    logger.info(f"probe2 for test_id={test_id} has {probe_status}")
    return not probe1


def forge1(splunk_client: SplunkClient, test_id: str) -> Dict[str, object]:
    logger.info(f"forge1 for test_id={test_id} started")
    splunk_client.method(test_id)
    return dict(
        forge1_test_id=test_id,
    )


def forge2(
    vendor_client: VendorClient, test_id: str, probe1: bool
) -> Dict[str, object]:
    logger.info(f"forge2 for test_id={test_id} started, probe1={probe1}")
    if probe1:
        vendor_client.method(test_id)
    return dict(
        forge2_test_id=test_id,
        forge2_probe1=probe1,
    )


@bootstrap(
    forge(forge1, probe=probe1),
    forge(forge2, probe=probe2),
)
def test_probes(
    test_id: str,
    forge1_test_id: str,
    forge2_test_id: str,
    probe1: bool,
    probe2: bool,
    forge2_probe1: bool,
) -> None:
    logger.info("test_probes execution started")
    assert test_id == forge1_test_id and test_id == forge2_test_id
    assert forge2_probe1 == probe1
    assert probe1 is True
    assert probe2 is False
