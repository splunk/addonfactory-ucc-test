import logging

from splunk_add_on_ucc_modinput_test.functional.decorators import (
    attach,
    forge,
)


logger = logging.getLogger("ucc-modinput-test")


def failing_forge() -> None:
    raise RuntimeError("attached forge failure")


@attach(forge(failing_forge))
def test_attached_forge_failure() -> None:
    logger.info("parent test body executed")
