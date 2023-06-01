from splunk_add_on_ucc_modinput_test.common import utils
import pytest

def test_get_from_environment_variable(monkeypatch):
    with pytest.raises(SystemExit) as e:
        utils.get_from_environment_variable("DOES_NOT_EXIST")
    assert e.type == SystemExit
    assert e.value.code == 1
    
    k = "EXISTING_ENV_VARIABLE"
    v = "some_value"
    monkeypatch.setenv(k, v)
    assert utils.get_from_environment_variable(k) == v
