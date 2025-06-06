from pathlib import Path
import shutil
from typing import Optional
from splunk_add_on_ucc_modinput_test.common import utils
import pytest
import tempfile


def test_get_from_environment_variable(monkeypatch) -> None:  # type: ignore
    with pytest.raises(utils.SplunkClientConfigurationException) as e:
        utils.get_from_environment_variable("DOES_NOT_EXIST")
    assert e.type == utils.SplunkClientConfigurationException
    # assert e.value.code == 1

    k = "EXISTING_ENV_VARIABLE"
    v = "some_value"
    monkeypatch.setenv(k, v)
    assert utils.get_from_environment_variable(k) == v


def test_get_from_env_var_string_function(monkeypatch) -> None:  # type: ignore
    some_str = "I am complex enough to be encoded"
    k = "ENV_VARIABLE_BASE64"
    v = utils.Base64.encode(some_str)
    monkeypatch.setenv(k, v)
    assert (
        utils.get_from_environment_variable(
            k, string_function=utils.Base64.decode
        )
        == some_str
    )


def test_get_from_environment_variable_optional() -> None:
    assert (
        utils.get_from_environment_variable("DOES_NOT_EXIST", is_optional=True)
        is None
    )


def test_get_from_environment_variable_default_value() -> None:
    v = "some_value"
    assert (
        utils.get_from_environment_variable("DOES_NOT_EXIST", default_value=v)
        == v
    )


def test_get_from_environment_variable_if_exists_and_default_defined(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    k = "EXISTING_ENV_VARIABLE"
    v = "some_value"
    monkeypatch.setenv(k, v)
    assert (
        utils.get_from_environment_variable(
            k, default_value="some default value"
        )
        == v
    )


def test_get_from_def_var_string_function(monkeypatch) -> None:  # type: ignore
    some_str = "I am complex enough to be encoded"
    dv = utils.Base64.encode(some_str)
    assert (
        utils.get_from_environment_variable(
            "DOES_NOT_EXIST",
            default_value=dv,
            string_function=utils.Base64.decode,
        )
        == some_str
    )


def test_base64() -> None:
    def _encode_decode_assert(
        input_string: str, expected: Optional[str] = None
    ) -> None:
        if expected is None:
            expected = input_string
        encoded_s = utils.Base64.encode(string=input_string)
        actual = utils.Base64.decode(base64_string=encoded_s)
        assert actual == expected

    _encode_decode_assert("I w@nt t0 encode th^s!")
    input_string = """Th!s
is
multiline"""
    _encode_decode_assert(input_string=input_string, expected=input_string)
    expected = """Th!s
is
multiline"""
    input_string = """Th!s
is
multiline



"""
    _encode_decode_assert(input_string=input_string, expected=expected)

    input_string = """Th!s

is

multiline"""
    _encode_decode_assert(input_string=input_string, expected=input_string)
    expected = """Th!s

is

multiline"""
    input_string = """Th!s

is

multiline



"""
    _encode_decode_assert(input_string=input_string, expected=expected)


def test_base64_remove_ending_chars() -> None:
    expected = ""

    input = expected
    actual = utils.Base64._remove_ending_chars(string=input)
    assert actual == expected

    input = """
"""
    actual = utils.Base64._remove_ending_chars(string=input)
    assert actual == expected

    input = """



"""
    actual = utils.Base64._remove_ending_chars(string=input)
    assert actual == expected


def test_find_common_prefix() -> None:
    assert (
        utils.find_common_prefix(
            [
                "/Splunk_TA_Example_account",
                r"/Splunk_TA_Example_account/\{name\}",
                "/Splunk_TA_Example_settings/proxy",
                "/Splunk_TA_Example_settings/logging",
                "/Splunk_TA_Example_settings/advanced_inputs",
                "/Splunk_TA_Example_example",
                r"/Splunk_TA_Example_example/\{name\}",
            ]
        )
        == "/Splunk_TA_Example_"
    )

    assert (
        utils.find_common_prefix(
            [
                "/Splunk_TA_Example_account",
                r"/Splunk_TA_Example_account/\{name\}",
                "/Splunk_TA_Example_settings/proxy",
            ]
        )
        == "/Splunk_TA_Example_"
    )


def test_md5():
    src_file = Path("tests/unit/resources/openapi.json")
    md5 = utils.md5(file_path=src_file)
    with tempfile.TemporaryDirectory() as temp_dir:
        copy_unchanged = Path(temp_dir) / "copy_unchanged.txt"
        copy_modified = Path(temp_dir) / "copy_modified.txt"

        shutil.copy(src_file, copy_unchanged)
        shutil.copy(src_file, copy_modified)
        copy_modified.write_text(copy_modified.read_text() + " modified")
        md5_unchanged = utils.md5(file_path=copy_unchanged)
        md5_unchanged_chunk_size_1024 = utils.md5(
            file_path=copy_unchanged, chunk_size=1024
        )
        md5_unchanged_chunk_size_32768 = utils.md5(
            file_path=copy_unchanged, chunk_size=32768
        )
        md5_modified = utils.md5(file_path=copy_modified)

    assert md5 == md5_unchanged
    assert md5 == md5_unchanged_chunk_size_1024
    assert md5 == md5_unchanged_chunk_size_32768
    assert md5 != md5_modified
