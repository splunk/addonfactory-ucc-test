import pytest
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
