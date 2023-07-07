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

def test_base64():

    def _encode_decode_assert(input_string: str, expected: str=None):
        if expected == None: expected = input_string
        encoded_s = utils.Base64.encode(string=input_string)
        actual = utils.Base64.decode(base64_string=encoded_s)
        assert actual == expected
    
    _encode_decode_assert('I w@nt t0 encode th^s!')
    input_string = '''Th!s
is
multiline'''
    _encode_decode_assert(input_string=input_string, expected=input_string)
    expected = '''Th!s
is
multiline'''
    input_string = '''Th!s
is
multiline



'''
    _encode_decode_assert(input_string=input_string, expected=expected)




    input_string = '''Th!s

is

multiline'''
    _encode_decode_assert(input_string=input_string, expected=input_string)
    expected = '''Th!s

is

multiline'''
    input_string = '''Th!s

is

multiline



'''
    _encode_decode_assert(input_string=input_string, expected=expected)

def test_base64_remove_ending_chars():

    expected = ''

    input = expected
    actual = utils.Base64._remove_ending_chars(string=input)
    assert actual == expected

    input = '''
'''
    actual = utils.Base64._remove_ending_chars(string=input)
    assert actual == expected

    input = '''



'''
    actual = utils.Base64._remove_ending_chars(string=input)
    assert actual == expected