import pytest
import logging

from splunk_add_on_ucc_modinput_test.functional.decorators import (
    bootstrap,
    forge,
)

logger = logging.getLogger("ucc-modinput-test")


def provide_selected_value(parametrized_value: str) -> dict[str, str]:
    logger.info(f"provide_selected_value value={parametrized_value}")
    return {"forged_value": parametrized_value}


@pytest.mark.parametrize(
    "parametrized_value",
    [
        pytest.param("selected", marks=pytest.mark.selected),
        pytest.param("deselected"),
    ],
)
@bootstrap(forge(provide_selected_value, scope="function"))
def test_partially_selected_parametrized(
    parametrized_value: str,
    forged_value: str,
) -> None:
    assert forged_value == parametrized_value
