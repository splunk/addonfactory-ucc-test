import pytest
from splunk_add_on_ucc_modinput_test.common.utils import logger

from splunk_add_on_ucc_modinput_test.functional.decorators import (
    bootstrap,
    forge,
)

from typing import Dict


def forge1(test_id: str, parametrized_param1: str) -> Dict[str, object]:
    logger.info(
        f"forge1 test_id={test_id}, parametrized_param1={parametrized_param1}"
    )

    return dict(forge1_parametrized_param1=parametrized_param1)


def forge2(test_id: str, parametrized_param2: str) -> Dict[str, object]:
    logger.info(
        f"forge2 test_id={test_id}, parametrized_param2={parametrized_param2}"
    )

    return dict(forge2_parametrized_param2=parametrized_param2)


@pytest.mark.parametrize(
    "parametrized_param1,parametrized_param2",
    [
        ("param1-1", "param2-1"),
        ("param-2", "param2-2"),
    ],
)
@bootstrap(
    forge(forge1),
    forge(forge2),
)
def test_parametrized(
    test_id: str,
    parametrized_param1: str,
    forge1_parametrized_param1: str,
    parametrized_param2: str,
    forge2_parametrized_param2: str,
) -> None:
    logger.info(f"test_parametrized test_id={test_id} execution")
    assert forge1_parametrized_param1 == parametrized_param1
    assert forge2_parametrized_param2 == parametrized_param2
