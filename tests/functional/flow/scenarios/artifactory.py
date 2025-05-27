from typing import Dict
from splunk_add_on_ucc_modinput_test.functional.decorators import (
    bootstrap,
    forge,
)
import logging

logger = logging.getLogger("ucc-modinput-test")


def forge1() -> Dict[str, object]:
    artifact = "forge1"
    overwrite_artifact = "forge1"
    logger.info(f"forge1 artifactory value: {artifact}")
    logger.info(f"forge1 overwrite_artifact value: {overwrite_artifact}")

    return dict(
        forge1_artifact=artifact,
        overwrite_artifact=overwrite_artifact,
    )


def forge2(overwrite_artifact: str) -> Dict[str, object]:
    artifact = "forge2"
    overwrite_artifact = f"{overwrite_artifact}+forge2"
    logger.info(f"forge2 artifactory value: {artifact}")
    logger.info(f"forge2 overwrite_artifact value: {overwrite_artifact}")

    return dict(
        forge2_artifact=artifact,
        overwrite_artifact=overwrite_artifact,
    )


@bootstrap(
    forge(forge1),
    forge(forge2),
)
def test_artifactory(
    forge1_artifact: str, forge2_artifact: str, overwrite_artifact: str
) -> None:
    logger.info("test_artifactory execution")
    assert forge1_artifact == "forge1"
    assert forge2_artifact == "forge2"
    assert overwrite_artifact == "forge1+forge2"
