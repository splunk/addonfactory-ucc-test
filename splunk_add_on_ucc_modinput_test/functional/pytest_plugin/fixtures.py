import pytest
from splunk_add_on_ucc_modinput_test.functional import logger
from splunk_add_on_ucc_modinput_test.functional.manager import (
    dependency_manager,
)
from splunk_add_on_ucc_modinput_test.functional.pytest_plugin.utils import (
    _extract_parametrized_data,
)


@pytest.fixture
def splunk_client(request):
    logger.debug(f"FIXTURE: create splunk client for {request}")
    yield dependency_manager.create_splunk_client()
    logger.debug(f"FIXTURE: teardown splunk client for {request}")


@pytest.fixture
def vendor_client(request):
    logger.debug(f"FIXTURE: create vendor client for {request}")
    yield dependency_manager.create_vendor_client()
    logger.debug(f"FIXTURE: teardown vendor client  for {request}")
