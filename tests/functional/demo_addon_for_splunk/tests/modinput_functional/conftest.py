#   DO NOT MODIFY CODE IN THIS FILE

from typing import Generator
import pytest
from splunk_add_on_ucc_modinput_test.common import conftest
from tests.modinput_functional.ta import Configuration as TaConfiguration

#   DO NOT MODIFY CODE IN THIS FILE


@pytest.fixture(scope="session")
def configuration(
    tmp_path_factory: pytest.TempPathFactory, worker_id: str
) -> Generator[TaConfiguration, None, None]:
    ta_configuration = conftest.setup(tmp_path_factory, worker_id)
    yield ta_configuration
    conftest.tear_down(ta_configuration, tmp_path_factory, worker_id)


#   DO NOT MODIFY CODE IN THIS FILE
