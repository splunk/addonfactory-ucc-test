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

def test_get_from_environment_variable_string_function(monkeypatch):
    some_str = 'I am complex enough to be encoded'
    k = 'ENV_VARIABLE_BASE64'
    v = utils.Base64.encode(some_str)
    monkeypatch.setenv(k, v)
    assert utils.get_from_environment_variable(k,string_function=utils.Base64.decode) == some_str

def test_get_from_environment_variable_optional(monkeypatch):
    assert utils.get_from_environment_variable("DOES_NOT_EXIST", is_optional=True) == None

# def test_get_from_environment_variable_alternative_environment_variable(monkeypatch):
#     k = 'DOES_NOT_EXIST'
#     k_alternative = "EXISTING_ENV_VARIABLE"
#     v_alternative = "some_value"
#     monkeypatch.setenv(k_alternative, v_alternative)
#     assert utils.get_from_environment_variable(k,alternative_environment_variable=k_alternative) == v_alternative
    
#     k = 'DOES_EXIST'
#     v = 'value'
#     monkeypatch.setenv(k, v)
#     assert utils.get_from_environment_variable(k,alternative_environment_variable=k_alternative) == v

# def test_get_from_environment_variable_alternative_with_function(monkeypatch):
#     k = 'DOES_NOT_EXIST'
#     k_alternative = "EXISTING_ENV_VARIABLE"
#     some_str = 'I am complex enough to be encoded'
#     v_alternative = utils.Base64.encode(some_str)
#     monkeypatch.setenv(k_alternative, v_alternative)
#     assert utils.get_from_environment_variable(k,alternative_environment_variable=k_alternative,string_function=utils.Base64.decode) == some_str