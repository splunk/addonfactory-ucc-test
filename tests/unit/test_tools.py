
import pytest
from pathlib import Path
from splunk_add_on_ucc_modinput_test import tools

def test_get_rest_root():
    assert tools.get_rest_root(openapi=Path("tests/unit/resources/openapi.json")) == 'Splunk_TA_Example'