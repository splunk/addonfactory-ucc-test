#
# Copyright 2025 Splunk Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import os
from filelock import FileLock
import json
import pytest  # noqa F401
from splunk_add_on_ucc_modinput_test.common import utils
from splunk_add_on_ucc_modinput_test.common.splunk_instance import (
    Configuration as SplunkConfiguration,
    MODINPUT_TEST_SPLUNK_INDEX_LOCK as MODINPUT_TEST_SPLUNK_INDEX_LOCK,
)
from tests.modinput_functional.vendor_product import (
    Configuration as VendorProductConfiguration,
)
from tests.modinput_functional.ta import Configuration as TaConfiguration


def create_ta_configuration_and_setup() -> TaConfiguration:
    if MODINPUT_TEST_SPLUNK_INDEX_LOCK in os.environ:
        raise OSError(
            f"Environment variable {MODINPUT_TEST_SPLUNK_INDEX_LOCK} set \
(value: {os.getenv(MODINPUT_TEST_SPLUNK_INDEX_LOCK)}) before \
new test run. Previous test failed most likely. \
Check the environment, unset the variable and run this \
test once again."
        )
    ta_configuration = TaConfiguration(
        splunk_configuration=SplunkConfiguration(),
        vendor_product_configuration=VendorProductConfiguration(),
    )
    ta_configuration.set_up(ta_configuration.api_instance)
    return ta_configuration


def setup(
    tmp_path_factory: pytest.TempPathFactory, worker_id: str
) -> TaConfiguration:
    # https://pytest-xdist.readthedocs.io/en/latest/how-to.html#making-session-scoped-fixtures-execute-only-once
    if worker_id == "master":
        ta_configuration = create_ta_configuration_and_setup()
        os.environ[
            MODINPUT_TEST_SPLUNK_INDEX_LOCK
        ] = ta_configuration.splunk_configuration.dedicated_index.name
    else:
        root_tmp_dir = tmp_path_factory.getbasetemp().parent
        fn = root_tmp_dir / "data.json"
        with FileLock(str(fn) + ".lock"):
            if fn.is_file():
                data = json.loads(fn.read_text())
                utils.Common().start_timestamp = float(data["start_timestamp"])
                os.environ[MODINPUT_TEST_SPLUNK_INDEX_LOCK] = data[
                    MODINPUT_TEST_SPLUNK_INDEX_LOCK
                ]
                ta_configuration = TaConfiguration(
                    splunk_configuration=SplunkConfiguration(),
                    vendor_product_configuration=VendorProductConfiguration(),
                )
                data["workers"].append(worker_id)
                fn.write_text(json.dumps(data))
            else:
                ta_configuration = create_ta_configuration_and_setup()
                index_name = (
                    ta_configuration.splunk_configuration.dedicated_index.name
                )
                data = {
                    "start_timestamp": utils.Common().start_timestamp,
                    "workers": [worker_id],
                    MODINPUT_TEST_SPLUNK_INDEX_LOCK: index_name,
                }
                fn.write_text(json.dumps(data))
    return ta_configuration


def ta_configuration_tear_down(ta_configuration: TaConfiguration) -> None:
    ta_configuration.tear_down(ta_configuration.api_instance)
    del os.environ[MODINPUT_TEST_SPLUNK_INDEX_LOCK]


def tear_down(
    ta_configuration: TaConfiguration,
    tmp_path_factory: pytest.TempPathFactory,
    worker_id: str,
) -> None:
    if worker_id == "master":
        ta_configuration_tear_down(ta_configuration=ta_configuration)
    else:
        root_tmp_dir = tmp_path_factory.getbasetemp().parent
        fn = root_tmp_dir / "data.json"
        data = json.loads(fn.read_text())
        if len(data["workers"]) == 1:
            ta_configuration_tear_down(ta_configuration=ta_configuration)
        else:
            data["workers"].remove(worker_id)
            fn.write_text(json.dumps(data))
